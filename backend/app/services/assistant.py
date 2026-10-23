"""AI shopping assistant: parse -> validate -> query DB -> (optionally) explain -> verified response.

The LLMs never touch the database or the cart. They only (1) turn text into a validated
ParsedRequest and (2) reword facts we already fetched. Prices, stock, totals and budget checks
are plain Python on database rows. Cart changes are returned as a pending_action the customer
must confirm; the frontend then calls the normal cart API, which validates again.

Replies are produced in the customer's UI language: templates via app/ai/messages.py, and the
response model is asked to write in that language.
"""
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.messages import HELP_EXAMPLES, t
from app.ai.ollama import OllamaClient, OllamaError
from app.ai.parser import is_adult_request, is_greeting, llm_parse, normalize, product_vocabulary, quick_parse
from app.ai.writer import write
from app.core.config import settings
from app.models import Product
from app.schemas.assistant import ChatRequest, ParsedRequest
from app.schemas.cart import MAX_LINE_QUANTITY
from app.schemas.catalog import ProductQuery
from app.services import cart as cart_service
from app.services import catalog

MAX_PRODUCTS = 8
MAX_BASKET_LINES = 6
NOT_MEDICAL_ADVICE = t("en", "not_medical")
GRAMS_PER_UNIT = {"kg": 1000, "500 g": 500, "250 g": 250}


def rupees(paise: int) -> str:
    return f"₹{paise // 100:,}" + (f".{paise % 100:02d}" if paise % 100 else "")


def describe(p: Product, lang: str = "en") -> str:
    stock = t(lang, "out_of_stock_short") if p.stock_quantity == 0 else t(lang, "in_stock", n=p.stock_quantity)
    return f"• {p.name}: {rupees(p.price_paise)} / {p.unit} ({stock})"


def category_word(category: str | None, lang: str) -> str:
    return t(lang, {"fruits": "what_fruits", "vegetables": "what_vegetables"}.get(category or "", "what_products"))


def first_match_per_keyword(db: Session, keywords: list[str], **filters) -> tuple[list[Product], list[str]]:
    found, missing = [], []
    for kw in keywords:
        hits = catalog.find_by_keyword(db, normalize(kw), **filters)
        if hits:
            found.append(hits[0])
        else:
            missing.append(kw)
    return list(dict.fromkeys(found)), missing


def to_product_units(p: Product, quantity: int, unit: str | None, lang: str = "en") -> tuple[int, str | None]:
    """Convert "2 kg" into the product's selling unit (e.g. 4 x "500 g")."""
    if unit in ("kg", "g") and p.unit in GRAMS_PER_UNIT:
        grams = quantity * (1000 if unit == "kg" else 1)
        per_unit = GRAMS_PER_UNIT[p.unit]
        units = max(1, -(-grams // per_unit))  # round up
        if p.unit == unit:  # "2 kg" of a per-kg product: nothing to explain
            return units, None
        rounded = t(lang, "rounded_up") if grams % per_unit else ""
        return units, t(lang, "unit_convert", name=p.name, unit=p.unit, qty=quantity, req_unit=unit, units=units, rounded=rounded)
    if unit and not p.unit.startswith(unit):
        return quantity, t(lang, "unit_mismatch", name=p.name, unit=p.unit, req_unit=unit, qty=quantity)
    return quantity, None


def stock_problem(p: Product, quantity: int, lang: str) -> str | None:
    """Same rules as cart_service.check_quantity, with a translated message."""
    if quantity > MAX_LINE_QUANTITY:
        return t(lang, "max_line", max=MAX_LINE_QUANTITY, unit=p.unit)
    if quantity > p.stock_quantity:
        return t(lang, "only_n_in_stock", n=p.stock_quantity, unit=p.unit, name=p.name) if p.stock_quantity else t(lang, "out_of_stock", name=p.name)
    return None


def product_facts(p: Product, nutrition) -> dict:
    facts = {
        "name": p.name, "category": p.category.name, "price": rupees(p.price_paise), "unit": p.unit,
        "in_stock": p.stock_quantity > 0, "description": p.description,
    }
    if p.original_price_paise:
        facts["price_before_discount"] = rupees(p.original_price_paise)
    if nutrition:
        facts["nutrition_per_100g"] = {
            k: getattr(nutrition, k) for k in (
                "energy_kcal", "protein_g", "carbohydrate_g", "fiber_g", "sugars_g",
                "fat_g", "vitamin_c_mg", "potassium_mg",
            ) if getattr(nutrition, k) is not None
        }
        facts["nutrition_source"] = nutrition.source_name
    return facts


def allowed_prices(products: list[Product]) -> set[int]:
    return {p.price_paise for p in products} | {p.original_price_paise for p in products if p.original_price_paise}


# --- intent handlers -------------------------------------------------------------------------

def handle_search(db: Session, parsed: ParsedRequest, lang: str = "en", **_) -> dict:
    filters = {"category": parsed.category, "max_price": parsed.budget_inr, "in_stock": parsed.in_stock_only}
    notes = []
    if parsed.keywords:
        products, missing = [], []
        for kw in parsed.keywords:
            hits = catalog.find_by_keyword(db, normalize(kw), **filters)
            products += hits
            if not hits:
                missing.append(kw)
        products = list(dict.fromkeys(products))
        total = len(products)
    else:
        sort = "price_asc" if parsed.budget_inr else "relevance"
        products, total = catalog.list_products(db, ProductQuery(**filters, sort=sort, page_size=MAX_PRODUCTS))
        missing = []
    products = products[:MAX_PRODUCTS]

    # Explain each keyword that found nothing: over budget, out of stock, or not sold at all.
    for kw in missing:
        unfiltered = catalog.find_by_keyword(db, normalize(kw))
        if not unfiltered:
            notes.append(t(lang, "not_sold_kw", kw=kw))
        elif parsed.budget_inr and unfiltered[0].price_paise > parsed.budget_inr * 100:
            p = unfiltered[0]
            notes.append(t(lang, "over_budget", name=p.name, price=rupees(p.price_paise), unit=p.unit, budget=parsed.budget_inr))
        elif unfiltered[0].stock_quantity == 0:
            notes.append(t(lang, "out_of_stock_now", name=unfiltered[0].name))
        else:
            notes.append(t(lang, "no_match_filters", kw=kw))

    what = category_word(parsed.category, lang)
    limit = t(lang, "under_limit", budget=parsed.budget_inr) if parsed.budget_inr else ""
    if products:
        count = t(lang, "count_of", shown=len(products), total=total) if total > len(products) else str(len(products))
        reply = t(lang, "here_are", count=count, what=what, limit=limit) + "\n" + "\n".join(describe(p, lang) for p in products)
    else:
        alternatives, _ = catalog.list_products(db, ProductQuery(
            category=parsed.category, in_stock=True, sort="price_asc", page_size=4,
        ))
        reply = t(lang, "not_found", what=what, limit=limit)
        if alternatives:
            reply += t(lang, "alternatives") + "\n" + "\n".join(describe(p, lang) for p in alternatives)
        products = alternatives
    if notes:
        reply += "\n\n" + " ".join(notes)
    return {"reply": reply, "products": products, "notes": notes}


def handle_nutrition(db: Session, ollama: OllamaClient, parsed: ParsedRequest, message: str, lang: str = "en", **_) -> dict:
    products, missing = first_match_per_keyword(db, parsed.keywords)
    not_medical = t(lang, "not_medical")
    if not products:
        reply = t(lang, "which_product_info")
        if missing:
            reply += " " + t(lang, "we_dont_sell_list", items=", ".join(missing))
        return {"reply": reply}
    refs = catalog.verified_nutrition(db, {p.nutrition_key for p in products if p.nutrition_key})
    nutrition = [{"product_id": p.id, "product_name": p.name, "nutrition": refs.get(p.nutrition_key)} for p in products]
    without = [p.name for p in products if p.nutrition_key not in refs]

    result = {"products": products, "nutrition": nutrition, "notes": [not_medical]}
    if len(without) == len(products):
        # Nothing verified to explain: do not let the model fill the gap from memory.
        result["reply"] = (
            t(lang, "no_verified_nutrition", names=", ".join(without)) + "\n"
            + "\n".join(f"{describe(p, lang)}\n  {p.description}" for p in products)
            + f"\n\n{not_medical}"
        )
        return result

    facts = {"products": [product_facts(p, refs.get(p.nutrition_key)) for p in products]}
    text = write(ollama, message, facts, allowed_prices(products), lang)
    if text:
        result.update(reply=f"{text}\n\n{not_medical}", writer=settings.ollama_response_model)
    else:
        result["reply"] = "\n".join(
            t(lang, "nutrition_line", name=p.name, source=refs[p.nutrition_key].source_name, values=", ".join(
                f"{k.replace('_', ' ')} {v}" for k, v in product_facts(p, refs[p.nutrition_key])["nutrition_per_100g"].items()
            )) if p.nutrition_key in refs else t(lang, "no_verified_short", name=p.name)
            for p in products
        ) + f"\n\n{not_medical}"
    if without:
        result["notes"].append(t(lang, "notes_no_verified", names=", ".join(without)))
    return result


def handle_compare(db: Session, ollama: OllamaClient, parsed: ParsedRequest, message: str, lang: str = "en", **_) -> dict:
    products, missing = first_match_per_keyword(db, parsed.keywords)
    note = " " + t(lang, "we_dont_sell_list", items=", ".join(missing)) if missing else ""
    if len(products) < 2:
        return {"reply": t(lang, "compare_need_two") + note, "products": products}
    refs = catalog.verified_nutrition(db, {p.nutrition_key for p in products if p.nutrition_key})
    facts = {"products": [product_facts(p, refs.get(p.nutrition_key)) for p in products]}
    if not refs:
        facts["note"] = "No verified nutrition data is available for these products."
    text = write(ollama, message, facts, allowed_prices(products), lang)
    result = {"products": products, "notes": [t(lang, "not_medical")] if refs else []}
    if text:
        result.update(reply=text + note, writer=settings.ollama_response_model)
    else:
        result["reply"] = t(lang, "side_by_side") + "\n" + "\n".join(describe(p, lang) for p in products) + note
    return result


def handle_budget_basket(db: Session, parsed: ParsedRequest, lang: str = "en", **_) -> dict:
    if not parsed.budget_inr:
        return {"reply": t(lang, "ask_budget")}
    budget = parsed.budget_inr * 100
    if parsed.keywords:
        candidates = []
        for kw in parsed.keywords:
            candidates += catalog.find_by_keyword(db, normalize(kw), category=parsed.category, in_stock=True)
    else:
        candidates, _ = catalog.list_products(db, ProductQuery(category=parsed.category, in_stock=True, page_size=60))

    # ponytail: greedy, one unit of each product in relevance order (featured, bestseller).
    # Swap for a knapsack/optimizer if customers want "maximise variety" or quantities > 1.
    picked, total = [], 0
    for p in dict.fromkeys(candidates):
        if len(picked) < MAX_BASKET_LINES and total + p.price_paise <= budget:
            picked.append((p, 1))
            total += p.price_paise

    what = category_word(parsed.category, lang)
    if not picked:
        cheapest = min(candidates, key=lambda p: p.price_paise, default=None)
        reply = t(lang, "cant_fit", what=what, budget=parsed.budget_inr)
        if cheapest:
            reply += t(lang, "cheapest", name=cheapest.name, price=rupees(cheapest.price_paise), unit=cheapest.unit)
        return {"reply": reply, "products": [cheapest] if cheapest else []}

    q = cart_service.quote(picked)
    assert q["total_paise"] <= budget  # guaranteed by the loop; guards future edits
    basket = {**q, "budget_paise": budget, "remaining_paise": budget - q["total_paise"]}
    reply = (
        t(lang, "basket_intro", what=what, budget=parsed.budget_inr) + "\n"
        + "\n".join(f"• {line['name']}: {rupees(line['line_total_paise'])} / {line['unit']}" for line in q["lines"])
        + "\n" + t(lang, "basket_total", total=rupees(q["total_paise"]), remaining=rupees(basket["remaining_paise"]))
        + "\n" + t(lang, "basket_cta")
    )
    return {
        "reply": reply,
        "products": [p for p, _ in picked],
        "basket": basket,
        "pending_action": {
            "items": [{"product_id": p.id, "quantity": qty} for p, qty in picked],
            "total_paise": q["total_paise"],
            "summary": t(lang, "basket_summary", n=len(picked), total=rupees(q["total_paise"])),
        },
    }


def handle_add_to_cart(db: Session, parsed: ParsedRequest, lang: str = "en", **_) -> dict:
    if not parsed.keywords:
        return {"reply": t(lang, "which_product_add")}
    picked, problems, notes = [], [], []
    for kw in parsed.keywords:
        hits = catalog.find_by_keyword(db, normalize(kw))
        if not hits:
            problems.append(t(lang, "not_sold_short", kw=kw))
            continue
        p = hits[0]
        quantity, note = to_product_units(p, parsed.quantity or 1, parsed.quantity_unit, lang)
        if problem := stock_problem(p, quantity, lang):
            problems.append(problem)
            continue
        picked.append((p, quantity))
        if note:
            notes.append(note)

    result = {"products": [p for p, _ in picked], "notes": notes}
    if not picked:
        result["reply"] = " ".join(problems) or t(lang, "cant_prepare")
        return result
    q = cart_service.quote(picked)
    items = ", ".join(f"{line['quantity']} x {line['unit']} {line['name']} ({rupees(line['line_total_paise'])})" for line in q["lines"])
    result["reply"] = " ".join([
        t(lang, "confirm_add", items=items, total=rupees(q["total_paise"])),
        t(lang, "nothing_added"), *notes, *problems,
    ])
    result["basket"] = q
    result["pending_action"] = {
        "items": [{"product_id": p.id, "quantity": qty} for p, qty in picked],
        "total_paise": q["total_paise"],
        "summary": t(lang, "add_summary", items=items),
    }
    return result


def handle_other(lang: str = "en", **_) -> dict:
    return {"reply": t(lang, "help") + "\n" + HELP_EXAMPLES}


HANDLERS = {
    "search": handle_search, "nutrition": handle_nutrition, "compare": handle_compare,
    "budget_basket": handle_budget_basket, "add_to_cart": handle_add_to_cart, "other": handle_other,
}

# Kept for callers/tests that refer to the English texts.
GREETING_REPLY = t("en", "greeting")
BLOCKED_REPLY = t("en", "blocked")


def chat(db: Session, ollama: OllamaClient, request: ChatRequest) -> dict:
    started = time.perf_counter()
    lang = request.lang

    # Checked first and without any model: adult requests are refused, greetings answered instantly.
    if is_adult_request(request.message) or is_greeting(request.message):
        return {
            "reply": t(lang, "blocked") if is_adult_request(request.message) else t(lang, "greeting"),
            "intent": "other", "parser": "rules", "writer": "template", "notes": [],
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }

    names = list(db.scalars(select(Product.name).where(Product.is_active)))
    vocabulary = product_vocabulary(names)

    notes = []
    parsed, parser = quick_parse(request.message, vocabulary), "rules"
    if parsed is None:
        try:
            parsed, parser = llm_parse(ollama, request.message, request.history), settings.ollama_intent_model
        except OllamaError as e:
            parsed, parser = quick_parse(request.message, vocabulary, strict=False), "fallback"
            notes.append(t(lang, "ai_unavailable", detail=e.detail))
            if parsed is None:
                parsed = ParsedRequest(intent="other")

    result = {"writer": "template", "notes": [], **HANDLERS[parsed.intent](
        db=db, ollama=ollama, parsed=parsed, message=request.message, lang=lang,
    )}
    result["notes"] = notes + result["notes"]
    return {**result, "intent": parsed.intent, "parser": parser,
            "duration_ms": int((time.perf_counter() - started) * 1000)}
