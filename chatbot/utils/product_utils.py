from difflib import get_close_matches
from chatbot.data.config import greetings
import re
from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rfuzz


def match_product_name(user_query, product_list, cutoff=0.6):
    """
    Fuzzy match user query to a product name from known list.
    Returns best match or None.
    """
    matches = get_close_matches(user_query.lower(), [p.lower() for p in product_list], n=1, cutoff=cutoff)
    if matches:
        for product in product_list:
            if product.lower() == matches[0]:
                return product
    return None



GENERIC_NAMES = {"mdb saalam", "mdb savings account", "mdb digital", "mdb saalam savings account"}

def extract_multiple_products(user_query, known_products, threshold=85):
    matched = []
    for product in known_products:
        score = rfuzz.partial_ratio(product.lower(), user_query.lower())
        if score >= threshold:
            matched.append((product, score))

    # Sort by descending score
    matched.sort(key=lambda x: -x[1])

    # Filter out generic or overly similar names
    top = []
    for prod, _ in matched:
        prod_lower = prod.lower()
        if prod_lower in GENERIC_NAMES:
            continue
        if all(rfuzz.ratio(prod_lower, other.lower()) < 92 for other in top):
            top.append(prod)
        if len(top) == 2:
            break

    return top


def summarize_context(context, llm_services, cache, history=None):
    summary_key = f"summary:{hash(context)}"
    if cache and summary_key in cache:
        return cache[summary_key]

    prompt = (
        f"Please summarize the following product details concisely:\n\n{context}\n\nSummary:"
    )
    messages = llm_services.build_message_list("Summarize product details", prompt, cache, history=history)
    summary = llm_services.get_gpt_response(messages, cache)

    print(f"📝 Summary returned ({len(summary)} chars): {summary[:300]}...")  # Add preview
    
    if cache is not None:
        cache[summary_key] = summary.strip()

    return summary.strip()


