"""Assistant reply templates in every supported UI language.

Template replies are translated deterministically (instant, and prices are inserted by code, so a
translation can never change them). Product names stay as stored in the database.
"""
from typing import Literal

Lang = Literal["en", "es", "ar", "hi"]
LANGUAGE_NAMES: dict[str, str] = {"en": "English", "es": "Spanish", "ar": "Arabic", "hi": "Hindi"}

MESSAGES: dict[str, dict[str, str]] = {
    "in_stock": {"en": "{n} in stock", "es": "{n} disponibles", "ar": "{n} متوفر", "hi": "{n} स्टॉक में"},
    "out_of_stock_short": {"en": "out of stock", "es": "agotado", "ar": "غير متوفر", "hi": "स्टॉक में नहीं"},
    "rounded_up": {"en": " (rounded up)", "es": " (redondeado hacia arriba)", "ar": " (مقرّب للأعلى)", "hi": " (ऊपर की ओर पूर्णांकित)"},
    "unit_convert": {
        "en": "{name} is sold per {unit}, so {qty} {req_unit} = {units} x {unit}{rounded}.",
        "es": "{name} se vende por {unit}, así que {qty} {req_unit} = {units} x {unit}{rounded}.",
        "ar": "يُباع {name} لكل {unit}، لذا {qty} {req_unit} = {units} × {unit}{rounded}.",
        "hi": "{name} {unit} के हिसाब से बिकता है, इसलिए {qty} {req_unit} = {units} x {unit}{rounded}।",
    },
    "unit_mismatch": {
        "en": "{name} is sold per {unit}, not per {req_unit}. I used {qty} x {unit}; change it if you meant something else.",
        "es": "{name} se vende por {unit}, no por {req_unit}. Usé {qty} x {unit}; cámbialo si querías otra cosa.",
        "ar": "يُباع {name} لكل {unit} وليس لكل {req_unit}. استخدمت {qty} × {unit}؛ غيّرها إذا كنت تقصد شيئًا آخر.",
        "hi": "{name} {unit} के हिसाब से बिकता है, {req_unit} के हिसाब से नहीं। मैंने {qty} x {unit} लिया है; अगर आप कुछ और चाहते थे तो बदल दें।",
    },
    "not_sold_kw": {"en": "We don't sell '{kw}' at the moment.", "es": "Por ahora no vendemos '{kw}'.", "ar": "لا نبيع '{kw}' حاليًا.", "hi": "हम अभी '{kw}' नहीं बेचते।"},
    "over_budget": {
        "en": "{name} costs {price} / {unit}, above your ₹{budget} limit.",
        "es": "{name} cuesta {price} / {unit}, por encima de tu límite de ₹{budget}.",
        "ar": "سعر {name} هو {price} / {unit}، وهو أعلى من حدّك البالغ ₹{budget}.",
        "hi": "{name} की कीमत {price} / {unit} है, जो आपकी ₹{budget} की सीमा से ज़्यादा है।",
    },
    "out_of_stock_now": {"en": "{name} is out of stock right now.", "es": "{name} está agotado en este momento.", "ar": "{name} غير متوفر حاليًا.", "hi": "{name} अभी स्टॉक में नहीं है।"},
    "no_match_filters": {"en": "No {kw} matched those filters.", "es": "Ningún resultado de {kw} coincide con esos filtros.", "ar": "لا يوجد {kw} يطابق هذه الفلاتر.", "hi": "इन फ़िल्टर से कोई {kw} मेल नहीं खाता।"},
    "what_fruits": {"en": "fruits", "es": "frutas", "ar": "فواكه", "hi": "फल"},
    "what_vegetables": {"en": "vegetables", "es": "verduras", "ar": "خضروات", "hi": "सब्ज़ियाँ"},
    "what_products": {"en": "products", "es": "productos", "ar": "منتجات", "hi": "उत्पाद"},
    "under_limit": {"en": " under ₹{budget}", "es": " por menos de ₹{budget}", "ar": " بأقل من ₹{budget}", "hi": " ₹{budget} से कम में"},
    "count_of": {"en": "{shown} of {total}", "es": "{shown} de {total}", "ar": "{shown} من {total}", "hi": "{total} में से {shown}"},
    "here_are": {"en": "Here are {count} {what}{limit}:", "es": "Aquí tienes {count} {what}{limit}:", "ar": "إليك {count} {what}{limit}:", "hi": "ये रहे {count} {what}{limit}:"},
    "not_found": {"en": "I couldn't find matching {what}{limit}.", "es": "No encontré {what}{limit} que coincidan.", "ar": "لم أجد {what}{limit} مطابقة.", "hi": "मुझे मेल खाते {what}{limit} नहीं मिले।"},
    "alternatives": {"en": " Some available alternatives:", "es": " Algunas alternativas disponibles:", "ar": " بعض البدائل المتوفرة:", "hi": " कुछ उपलब्ध विकल्प:"},
    "which_product_info": {
        "en": "Which fruit or vegetable would you like to know about?",
        "es": "¿Sobre qué fruta o verdura quieres saber?",
        "ar": "عن أي فاكهة أو خضار تريد أن تعرف؟",
        "hi": "आप किस फल या सब्ज़ी के बारे में जानना चाहते हैं?",
    },
    "we_dont_sell_list": {"en": "We don't sell {items}.", "es": "No vendemos {items}.", "ar": "لا نبيع {items}.", "hi": "हम {items} नहीं बेचते।"},
    "no_verified_nutrition": {
        "en": "I don't have verified nutrition data for {names} yet, so I won't guess nutrient amounts, benefits or limitations. Here is what I can tell you from our catalog:",
        "es": "Todavía no tengo datos nutricionales verificados de {names}, así que no adivinaré nutrientes, beneficios ni limitaciones. Esto es lo que puedo contarte de nuestro catálogo:",
        "ar": "ليست لدي بيانات غذائية موثّقة عن {names} بعد، لذلك لن أخمّن العناصر الغذائية أو الفوائد أو القيود. هذا ما يمكنني إخبارك به من كتالوجنا:",
        "hi": "मेरे पास {names} का सत्यापित पोषण डेटा अभी नहीं है, इसलिए मैं पोषक तत्वों, फ़ायदों या सीमाओं का अनुमान नहीं लगाऊँगा। हमारे कैटलॉग से मैं यह बता सकता हूँ:",
    },
    "not_medical": {
        "en": "This is general information, not medical advice.",
        "es": "Esta es información general, no consejo médico.",
        "ar": "هذه معلومات عامة وليست نصيحة طبية.",
        "hi": "यह सामान्य जानकारी है, चिकित्सीय सलाह नहीं।",
    },
    "nutrition_line": {"en": "{name} per 100 g ({source}): {values}", "es": "{name} por 100 g ({source}): {values}", "ar": "{name} لكل 100 غ ({source}): {values}", "hi": "{name} प्रति 100 ग्राम ({source}): {values}"},
    "no_verified_short": {"en": "{name}: no verified nutrition data yet.", "es": "{name}: aún sin datos nutricionales verificados.", "ar": "{name}: لا توجد بيانات غذائية موثّقة بعد.", "hi": "{name}: अभी सत्यापित पोषण डेटा नहीं है।"},
    "notes_no_verified": {"en": "No verified nutrition data yet for: {names}.", "es": "Aún sin datos nutricionales verificados para: {names}.", "ar": "لا توجد بيانات غذائية موثّقة بعد لـ: {names}.", "hi": "इनका सत्यापित पोषण डेटा अभी नहीं है: {names}।"},
    "compare_need_two": {
        "en": "Tell me two products to compare, for example 'compare apples and oranges'.",
        "es": "Dime dos productos para comparar, por ejemplo 'compare apples and oranges'.",
        "ar": "أخبرني بمنتجين للمقارنة، مثلًا 'compare apples and oranges'.",
        "hi": "तुलना के लिए दो उत्पाद बताइए, जैसे 'compare apples and oranges'।",
    },
    "side_by_side": {"en": "Side by side (demo prices):", "es": "Comparación (precios de demostración):", "ar": "مقارنة جنبًا إلى جنب (أسعار تجريبية):", "hi": "साथ-साथ तुलना (डेमो कीमतें):"},
    "ask_budget": {
        "en": "What is your budget? For example: 'suggest fruits within ₹500'.",
        "es": "¿Cuál es tu presupuesto? Por ejemplo: 'suggest fruits within ₹500'.",
        "ar": "ما ميزانيتك؟ مثلًا: 'suggest fruits within ₹500'.",
        "hi": "आपका बजट क्या है? उदाहरण: 'suggest fruits within ₹500'।",
    },
    "cant_fit": {"en": "I couldn't fit any {what} into ₹{budget}.", "es": "No pude incluir {what} dentro de ₹{budget}.", "ar": "لم أتمكن من إدخال أي {what} ضمن ₹{budget}.", "hi": "₹{budget} में कोई {what} नहीं आ सके।"},
    "cheapest": {"en": " The cheapest option is {name} at {price} / {unit}.", "es": " La opción más barata es {name} a {price} / {unit}.", "ar": " أرخص خيار هو {name} بسعر {price} / {unit}.", "hi": " सबसे सस्ता विकल्प {name} है, {price} / {unit}।"},
    "basket_intro": {
        "en": "Here is a basket of {what} within ₹{budget} (one unit each):",
        "es": "Aquí tienes una cesta de {what} dentro de ₹{budget} (una unidad de cada uno):",
        "ar": "إليك سلة {what} ضمن ₹{budget} (وحدة واحدة من كل منتج):",
        "hi": "₹{budget} के भीतर {what} की यह टोकरी है (हर एक की एक इकाई):",
    },
    "basket_total": {
        "en": "Total: {total}, leaving {remaining} of your budget.",
        "es": "Total: {total}; te quedan {remaining} de tu presupuesto.",
        "ar": "الإجمالي: {total}، ويتبقى {remaining} من ميزانيتك.",
        "hi": "कुल: {total}, आपके बजट में {remaining} बचे।",
    },
    "basket_cta": {
        "en": "Confirm below if you'd like these. Nothing has been added yet.",
        "es": "Confirma abajo si los quieres. Todavía no se ha añadido nada.",
        "ar": "أكّد بالأسفل إذا أردتها. لم تتم إضافة أي شيء بعد.",
        "hi": "अगर आपको ये चाहिए तो नीचे पुष्टि करें। अभी कुछ भी नहीं जोड़ा गया है।",
    },
    "basket_summary": {"en": "Add {n} items ({total}) to cart", "es": "Añadir {n} artículos ({total}) al carrito", "ar": "أضف {n} منتجات ({total}) إلى السلة", "hi": "{n} आइटम ({total}) कार्ट में जोड़ें"},
    "which_product_add": {
        "en": "Which product should I add? For example: 'add 2 kg of apples to my cart'.",
        "es": "¿Qué producto añado? Por ejemplo: 'add 2 kg of apples to my cart'.",
        "ar": "أي منتج أضيف؟ مثلًا: 'add 2 kg of apples to my cart'.",
        "hi": "मैं कौन सा उत्पाद जोड़ूँ? उदाहरण: 'add 2 kg of apples to my cart'।",
    },
    "not_sold_short": {"en": "We don't sell '{kw}'.", "es": "No vendemos '{kw}'.", "ar": "لا نبيع '{kw}'.", "hi": "हम '{kw}' नहीं बेचते।"},
    "only_n_in_stock": {"en": "Only {n} x {unit} of {name} in stock.", "es": "Solo hay {n} x {unit} de {name} disponibles.", "ar": "المتوفر من {name} هو {n} × {unit} فقط.", "hi": "{name} के केवल {n} x {unit} स्टॉक में हैं।"},
    "out_of_stock": {"en": "{name} is out of stock.", "es": "{name} está agotado.", "ar": "{name} غير متوفر.", "hi": "{name} स्टॉक में नहीं है।"},
    "max_line": {"en": "At most {max} x {unit} of one product per order.", "es": "Máximo {max} x {unit} de un producto por pedido.", "ar": "الحد الأقصى {max} × {unit} من المنتج الواحد في كل طلب.", "hi": "एक ऑर्डर में एक उत्पाद के अधिकतम {max} x {unit}।"},
    "cant_prepare": {"en": "I couldn't prepare that cart change.", "es": "No pude preparar ese cambio en el carrito.", "ar": "لم أتمكن من تجهيز هذا التغيير في السلة.", "hi": "मैं कार्ट में यह बदलाव तैयार नहीं कर सका।"},
    "confirm_add": {
        "en": "Please confirm: add {items} to your cart? Total {total}.",
        "es": "Confirma, por favor: ¿añadir {items} a tu carrito? Total {total}.",
        "ar": "يرجى التأكيد: هل أضيف {items} إلى سلتك؟ الإجمالي {total}.",
        "hi": "कृपया पुष्टि करें: {items} आपकी कार्ट में जोड़ें? कुल {total}।",
    },
    "nothing_added": {"en": "Nothing has been added yet.", "es": "Todavía no se ha añadido nada.", "ar": "لم تتم إضافة أي شيء بعد.", "hi": "अभी कुछ भी नहीं जोड़ा गया है।"},
    "add_summary": {"en": "Add {items}", "es": "Añadir {items}", "ar": "أضف {items}", "hi": "{items} जोड़ें"},
    "help": {
        "en": "I can help you shop for fruits and vegetables. Try:",
        "es": "Puedo ayudarte a comprar frutas y verduras. Prueba:",
        "ar": "يمكنني مساعدتك في شراء الفواكه والخضروات. جرّب:",
        "hi": "मैं फल और सब्ज़ियाँ खरीदने में आपकी मदद कर सकता हूँ। ये आज़माएँ:",
    },
    "greeting": {
        "en": "Hi! How can I assist you today?",
        "es": "¡Hola! ¿En qué puedo ayudarte hoy?",
        "ar": "مرحبًا! كيف يمكنني مساعدتك اليوم؟",
        "hi": "नमस्ते! आज मैं आपकी क्या मदद कर सकता हूँ?",
    },
    "blocked": {
        "en": "Sorry, we don't support this kind of question. I can help you with fruits, vegetables, prices and your cart.",
        "es": "Lo siento, no admitimos este tipo de preguntas. Puedo ayudarte con frutas, verduras, precios y tu carrito.",
        "ar": "عذرًا، لا ندعم هذا النوع من الأسئلة. يمكنني مساعدتك في الفواكه والخضروات والأسعار وسلتك.",
        "hi": "क्षमा करें, हम इस तरह के सवालों का समर्थन नहीं करते। मैं फल, सब्ज़ियों, कीमतों और आपकी कार्ट में मदद कर सकता हूँ।",
    },
    "ai_unavailable": {
        "en": "The AI model is unavailable ({detail}) so I used a simple search.",
        "es": "El modelo de IA no está disponible ({detail}), así que hice una búsqueda simple.",
        "ar": "نموذج الذكاء الاصطناعي غير متاح ({detail})، لذلك استخدمت بحثًا بسيطًا.",
        "hi": "AI मॉडल उपलब्ध नहीं है ({detail}), इसलिए मैंने सामान्य खोज की।",
    },
}

# Example prompts stay in English: the intent model and rules understand English best.
HELP_EXAMPLES = (
    "• 'Show me fruits below ₹200'\n• 'Compare apples and oranges'\n"
    "• 'Suggest fruits for my family within ₹500'\n• 'Add 2 kg of apples to my cart'"
)


def t(lang: str, key: str, **values) -> str:
    templates = MESSAGES[key]
    return templates.get(lang, templates["en"]).format(**values)
