"""Optional multi-agent workflow (Stage 8). Requires `pip install crewai` (see docs/crewai.md).

    discovery agent  --search_products-->  candidate products
    nutrition agent  --get_nutrition---->  short notes (verified data only)
    basket agent     --quote_basket----->  proposed product ids + quantities
    validate_basket (plain Python)       ->  real products, stock, budget, totals  -> pending_action

The agents only see read-only tools. Prices, stock, totals and the cart stay under backend control:
the final proposal is re-validated here and returned as a pending_action the customer must confirm.
"""
import logging
import os
import re
import time

# Must be set before crewai is imported: no telemetry or tracing data leaves this machine.
for _flag in ("OTEL_SDK_DISABLED", "CREWAI_DISABLE_TELEMETRY", "CREWAI_DISABLE_TRACKING"):
    os.environ.setdefault(_flag, "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from app.ai.ollama import OllamaClient, OllamaError  # noqa: E402
from app.ai.parser import normalize  # noqa: E402
from app.ai.writer import mentions_unknown_price  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.errors import ServiceError  # noqa: E402
from app.crew import tools  # noqa: E402
from app.crew.validation import validate_basket  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.schemas.catalog import ProductOut  # noqa: E402
from app.services import catalog  # noqa: E402
from app.services.assistant import NOT_MEDICAL_ADVICE, rupees  # noqa: E402

logger = logging.getLogger("kadai.crew")
AMOUNT = re.compile(r"(?:₹|\brs\.?|\binr)\s*(\d{1,6})", re.IGNORECASE)
BENEFITS_WORDS = ("healthy", "health", "nutrition", "vitamin", "family", "week", "plan", "balanced", "diet")


# Only the final task is structured. Measured: llama3.2 copied whole tool rows into a strict
# `product_ids: list[int]` field, and the failed conversion crashed the run after ~6 minutes.
# Intermediate steps therefore pass plain text, and the final schema is deliberately lenient:
# extra keys are ignored, and a product may be given by name, which resolve_items() looks up in the DB.
class ProposedItem(BaseModel):
    product_id: int | str
    quantity: int = 1


class BasketProposal(BaseModel):
    items: list[ProposedItem] = Field(default=[], max_length=12)
    explanation: str = ""


class CrewFailed(ServiceError):
    status_code = 502


def resolve_items(items: list[ProposedItem]) -> list[tuple[int, int]]:
    """Turn the planner's items into (product_id, quantity) using only database lookups."""
    resolved = []
    with SessionLocal() as db:
        for item in items:
            ref = str(item.product_id).strip()
            if ref.isdigit():
                product_id = int(ref)
            else:
                hits = catalog.find_by_keyword(db, normalize(ref[:40]), in_stock=True)
                if not hits:
                    continue  # unknown name: dropped, validate_basket never sees it
                product_id = hits[0].id
            resolved.append((product_id, max(1, min(int(item.quantity), 50))))
    return resolved


@tool("search_products")
def search_products_tool(keyword: str = "", category: str = "", max_price_inr: int = 0) -> list[dict]:
    """Search the Kad AI product database. keyword: a product name like 'apple' (optional).
    category: 'fruits' or 'vegetables' (optional). max_price_inr: price limit per unit (0 = none).
    Returns in-stock products with exact prices. Never invent products that this tool did not return."""
    return tools.search_products(keyword, category, max_price_inr)


@tool("get_nutrition")
def get_nutrition_tool(product_id: int) -> dict:
    """Verified nutrition data for one product id. If it says data is not available, say so; never guess."""
    return tools.get_nutrition(product_id)


@tool("quote_basket")
def quote_basket_tool(product_ids: list[int], quantities: list[int], budget_inr: int = 0) -> dict:
    """Check a basket: product_ids and quantities are parallel lists. Returns the authoritative total
    and whether it is within budget_inr. Always use this total; never calculate totals yourself."""
    return tools.quote_basket(product_ids, quantities, budget_inr)


def crew_recommended(message: str) -> bool:
    """A crew is worth its extra latency only when the request needs several kinds of work:
    a budget AND a goal like nutrition or family planning. Everything else suits the direct assistant."""
    text = message.lower()
    return bool(AMOUNT.search(message)) and any(w in text for w in BENEFITS_WORDS)


def _build(budget_text: str):
    # Measured on an 8 GB CPU laptop: without limits one /v1 request generated for 10 minutes (the
    # OpenAI client's default 600 s timeout); with 90 s, cold requests with CrewAI's long prompts
    # timed out. 150 s per request, capped output, no silent retries.
    llm = LLM(
        model=f"ollama/{settings.ollama_crew_model}", base_url=settings.ollama_base_url,
        temperature=0.2, max_tokens=500, timeout=150, max_retries=0,
    )
    # 300 s per agent: a single discovery call with CrewAI's ~2,000-token prompt took 127 s on CPU.
    common = {"llm": llm, "allow_delegation": False, "max_iter": 3, "max_execution_time": 300, "verbose": False}
    discovery = Agent(
        role="Product discovery specialist",
        goal="Find in-stock products in the Kad AI catalog that match the customer's request",
        backstory="You only know products returned by the search_products tool. You never invent products or prices.",
        tools=[search_products_tool], **common,
    )
    nutrition = Agent(
        role="Nutrition information assistant",
        goal="Write short, general nutrition notes for the chosen products using only verified data",
        backstory="You call get_nutrition for each product. If data is unavailable you say so plainly. "
                  "You never make medical claims or say a food cures or prevents anything.",
        tools=[get_nutrition_tool], **common,
    )
    planner = Agent(
        role="Budget and basket planner",
        goal="Choose products and quantities that fit the customer's budget",
        backstory="You check every basket with quote_basket. Only the tool's total is valid. "
                  "You keep a little variety: several different products, usually one unit each.",
        tools=[quote_basket_tool], **common,
    )
    find = Task(
        description="Customer request: {request}\nBudget: {budget}\n"
                    "Use search_products (call it a few times with different keywords or a category) "
                    "to find up to 6 suitable in-stock products.",
        expected_output="A short list of the products found, each with its product_id and name.",
        agent=discovery,
    )
    notes = Task(
        description="For the products found, call get_nutrition for each product id and write one short "
                    "general note per product. If there is no verified data, write 'No verified nutrition data for <name>.'",
        expected_output="Short notes, one line per product.",
        agent=nutrition, context=[find],
    )
    plan = Task(
        description=f"Build a basket from the products found that fits the budget ({budget_text}). Call quote_basket "
                    "to check it and adjust until within_budget is true. Then explain the choice in 2-3 sentences "
                    "without stating any prices or totals.",
        expected_output="Basket items (product_id and quantity) and a short explanation.",
        agent=planner, context=[find, notes], output_pydantic=BasketProposal,
    )
    crew = Crew(
        agents=[discovery, nutrition, planner], tasks=[find, notes, plan], process=Process.sequential,
        memory=False, tracing=False, share_crew=False, verbose=False,
    )
    return crew, [find, notes, plan]


def run_crew(message: str, budget_inr: int | None, ollama: OllamaClient) -> dict:
    started = time.perf_counter()
    if budget_inr is None and (m := AMOUNT.search(message)):
        budget_inr = int(m.group(1))
    budget_text = f"₹{budget_inr} total" if budget_inr else "no fixed budget"

    crew, (find, notes, plan) = _build(budget_text)
    try:
        with ollama.exclusive(settings.ollama_crew_model):  # one model in RAM, no parallel direct-chat calls
            out = crew.kickoff(inputs={"request": message, "budget": budget_text})
    except OllamaError:
        raise
    except Exception as e:  # CrewAI/LLM failures (bad output, tool loops): report, never a raw 500
        logger.warning("crew run failed: %s", type(e).__name__)
        raise CrewFailed("The shopping crew could not produce a valid answer this time. "
                         "Please try again or use the regular assistant.")

    proposal = out.pydantic if isinstance(out.pydantic, BasketProposal) else None
    items = resolve_items(proposal.items) if proposal else []
    nutrition_text = notes.output.raw if notes.output else ""

    # Final validation step: deterministic, never an LLM.
    with SessionLocal() as db:
        checked = validate_basket(db, items, budget_inr * 100 if budget_inr else None)
        # Serialize while the session is open: Product.category is lazy-loaded.
        product_cards = [ProductOut.model_validate(p).model_dump() for p in checked["products"]]

    result_notes = list(checked["problems"])
    explanation = proposal.explanation.strip() if proposal else ""
    allowed = {p.price_paise for p in checked["products"]} | {checked["total_paise"]}
    if explanation and mentions_unknown_price(explanation, allowed):
        explanation = ""
        result_notes.append("The planner's explanation mentioned prices that are not in our database, so it was removed.")
    # The agents don't always agree (measured: notes covered products the planner dropped), so keep
    # only whole lines about products that are actually in the validated basket.
    basket_words = {w for p in checked["products"] for w in p.name.lower().replace("(", " ").split() if len(w) > 3}
    note_lines = [
        line.strip(" -*•\t")[:200] for line in nutrition_text.splitlines()
        if any(w in line.lower() for w in basket_words) and not mentions_unknown_price(line, allowed)
    ][:8]

    parts = [explanation or "Here is a basket put together by the shopping crew."]
    if checked["lines"]:
        parts.append("\n".join(f"• {l['quantity']} x {l['unit']} {l['name']}: {rupees(l['line_total_paise'])}" for l in checked["lines"]))
        parts.append(f"Total {rupees(checked['total_paise'])} (checked by our server). Nothing has been added to your cart yet.")
    else:
        parts.append("The crew could not produce a valid basket. Try the regular assistant or a different budget.")
    if note_lines:
        parts.append("Nutrition notes:\n" + "\n".join(f"• {n}" for n in note_lines) + f"\n{NOT_MEDICAL_ADVICE}")

    for task, label in ((find, "Product discovery"), (notes, "Nutrition notes"), (plan, "Basket planning")):
        if task.start_time and task.end_time:
            result_notes.append(f"{label} agent: {(task.end_time - task.start_time).total_seconds():.0f}s")
    if not crew_recommended(message):
        result_notes.append("Tip: this request is simple enough for the regular assistant, which is much faster.")

    basket = {k: checked[k] for k in ("lines", "total_paise", "budget_paise", "remaining_paise")} if checked["lines"] else None
    return {
        "reply": "\n\n".join(parts),
        "intent": "budget_basket",
        "products": product_cards,
        "basket": basket,
        "pending_action": {
            "items": [{"product_id": l["product_id"], "quantity": l["quantity"]} for l in checked["lines"]],
            "total_paise": checked["total_paise"],
            "summary": f"Add {len(checked['lines'])} items ({rupees(checked['total_paise'])}) to cart",
        } if checked["lines"] else None,
        "notes": result_notes,
        "parser": "crewai",
        "writer": f"crewai:{settings.ollama_crew_model}",
        "duration_ms": int((time.perf_counter() - started) * 1000),
    }
