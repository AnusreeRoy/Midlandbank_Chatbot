from chatbot.services.retrieval_services import collection
from chatbot.utils.product_utils import match_product_name
import re
# from chatbot.utils.text_utils import clean_response
def list_products_grouped_by_category():
    """Group all products by category using ChromaDB metadata."""
    try:
        data = collection.get(include=["metadatas"])
        grouped = {}
        for meta in data["metadatas"]:
            title = meta.get("title", "").strip()
            category = meta.get("category", "general").strip().title()
            if title and "MDB" in title:
                cleaned_title = clean_title(title)
                grouped.setdefault(category, set()).add(cleaned_title)
        return {k: sorted(v) for k, v in grouped.items()}
    except Exception as e:
        print(f"Error grouping products: {e}")
        return {}

def clean_title(title):
    return title.replace("– Midland Bank PLC.", "").strip()

def list_products_by_category(category):
    grouped = list_products_grouped_by_category()
    return sorted(list(grouped.get(category.title(), [])))


def get_all_product_names():
    """Returns a flat list of all product names across categories."""
    grouped = list_products_grouped_by_category()
    all_products = set()
    for products in grouped.values():
        all_products.update(products)
    return sorted(all_products)


def list_islamic_products_grouped():
    """Return Islamic products grouped into inferred subcategories like Savings and Loan."""
    all_islamic = list_products_by_category("Islamic")

    grouped = {
        "Savings": [],
        "Loan": [],
        "Current": []
    }

    for title in all_islamic:
        lower_title = title.lower()
        if any(keyword in lower_title for keyword in ["savings", "deposit", "digital", "scheme","sthaee","sathi","super saver","family support","e-saver", "snd","super high performance"]):
            grouped["Savings"].append(title)
        elif any(keyword in lower_title for keyword in ["loan", "finance", "bai muajjal", "melk","nirman","amar bari"]):
            grouped["Loan"].append(title)
        elif any(keyword in lower_title for keyword in ["current account", "corporate payroll package", "abiram","saalam personal retail"]):
            grouped["Current"].append(title)

    return grouped


def get_sme_product_names():
    VALID_SME_PRODUCTS = {
        "MDB Abiram", "MDB Diptimoyi", "MDB Green", "MDB IT",
        "MDB Krishi", "MDB NGO", "MDB Nirbhorota", "MDB Nirman",
        "MDB Ogroj", "MDB Orjon", "MDB Praromvik", "MDB Property", "MDB Start-up"
    }

    loan_docs = collection.get(
        where={"category": "Loan"},
        include=["documents", "metadatas"]
    )

    raw_matches = set()

    # Extract and normalize matches
    for doc, meta in zip(loan_docs["documents"], loan_docs["metadatas"]):
        if meta.get("sub_category") == "SME":
            matches = re.findall(r"MDB [A-Z][a-zA-Z()\-]+", doc)
            for match in matches:
                normalized = match.title().replace("Mdb", "MDB")
                raw_matches.add(normalized)

    # ✅ Filter only valid SME products
    filtered_products = {p for p in raw_matches if p in VALID_SME_PRODUCTS}

    return sorted(filtered_products)


def get_nrb_product_names():
    
    VALID_NRB_PRODUCTS = {
    "MDB Probashi Savings","MDB NFCD Account","MDB FC Account","Wage Earner's Development Bond (WEDB)",
    "US Dollar Investment Bond","US Dollar Premium Bond","MDB Foreign Remittence Service","MDB Student File Service"
    }

    savings_docs = collection.get(
        where={"category": "savings"},
        include=["documents"]
    )

    product_names = set()

    for doc in savings_docs["documents"]:
        for product in VALID_NRB_PRODUCTS:
            if product.lower() in doc.lower():
                product_names.add(product)

    return sorted(product_names)


def is_product_list_request(message: str) -> bool:
    message = message.lower()
    product_list_phrases = [
        "other savings", "more savings", "other accounts", "what else", 
        "more options", "other products", "other loan", "show me more",
        "do you have other", "list all", "different accounts"
    ]
    return any(phrase in message for phrase in product_list_phrases)


def is_charge_query(text: str) -> bool:
    charge_keywords = [
        "fee", "charge", "vat", "excise", "maintenance", "closure",
        "a/c", "cheque book", "closing charge", "deposit", "locker charge",
        "certificate of tax", "processing fee", "transaction fee","settlement fee",
        "reschedule fee", "stamp charge", "penal interest", "sms alert", "npsb-ibft fees"
    ]
    return any(k in text.lower() for k in charge_keywords)



