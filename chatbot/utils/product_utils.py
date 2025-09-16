from difflib import get_close_matches
from chatbot.data.config import greetings
import re
from fuzzywuzzy import fuzz


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


def extract_multiple_products(user_query, known_products, threshold=85):
    """Fuzzy match multiple products in a query."""
    matched = []
    for product in known_products:
        score = fuzz.partial_ratio(product.lower(), user_query.lower())
        if score >= threshold:
            matched.append((product, score))
    matched.sort(key=lambda x: -x[1])
    return [name for name, _ in matched]


def summarize_context(context, llm_services, cache, history=None):
    prompt = (
        f"Please summarize the following product details concisely:\n\n{context}\n\nSummary:"
    )
    messages = llm_services.build_message_list("Summarize product details", prompt, cache, history=history)
    summary = llm_services.get_gpt_response(messages, cache)
    return summary.strip()
