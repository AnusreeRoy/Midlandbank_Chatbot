from chatbot.services.retrieval_services import collection
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

