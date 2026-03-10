from difflib import get_close_matches
from chatbot.data.config import greetings
import re
from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rfuzz


def match_product_name(user_query, product_list, cutoff=0.6):
    query = user_query.lower().strip()

    # Extract alphabetic word tokens (len > 2)
    q_tokens = [t for t in re.findall(r"[a-zA-Z]+", query) if len(t) > 2]

    # ---- HARD FILTER: No shared meaningful word → reject immediately ----
    filtered_products = []
    for product in product_list:
        p = product.lower()

        # check if any meaningful word appears in product name
        if any(t in p for t in q_tokens):
            filtered_products.append(product)

    # If nothing passes the word-overlap rule → NO MATCH
    if not filtered_products:
        return None

    # ---- Now do fuzzy match ONLY on the filtered products ----
    product_names_lower = [p.lower() for p in filtered_products]

    matches = get_close_matches(query, product_names_lower, n=1, cutoff=cutoff)

    if matches:
        for product in filtered_products:
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

   # 2️⃣ Filter out generic names
    filtered = [p for p, _ in matched if p.lower() not in GENERIC_NAMES]

    if not filtered:
        return []  # No relevant products found

    # 3️⃣ Decide if the user asked for multiple products
    multiple_products_intent = any(x in user_query.lower() for x in [" and ", "&", ",", " vs ", "compare", "difference", "between"])

    # 4️⃣ Return single or multiple products
    if multiple_products_intent:
        # Return up to 2 distinct products
        top = []
        for prod in filtered:
            if all(rfuzz.ratio(prod.lower(), other.lower()) < 92 for other in top):
                top.append(prod)
            if len(top) == 2:
                break
        return top
    else:
        # Single-product query → return only the best match
        return [filtered[0]]


def summarize_context(context, llm_services, cache, history=None):
    summary_key = f"summary:{hash(context)}"
    if cache and summary_key in cache:
        return cache[summary_key]

    prompt = (
        f"Please summarize the following product details in 3-5 bullet points, focusing on the key features, "
        f"eligibility, and benefits. Keep the summary short and concise.\n\n{context}\n\nSummary:"
    )
    messages = llm_services.build_message_list("Summarize product details", prompt, cache, history=history)
    summary = llm_services.get_gpt_response(messages, cache)

    print(f"📝 Summary returned ({len(summary)} chars): {summary[:300]}...")  # Add preview
    
    if cache is not None:
        cache[summary_key] = summary.strip()

    return summary.strip()


