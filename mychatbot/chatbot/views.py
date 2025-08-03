# from django.http import JsonResponse
# from rest_framework.decorators import api_view

# @api_view(['GET', 'POST'])
# def chatbot_response(request):
#     if request.method == 'POST':
#         user_message = request.data.get("message", "")
#         response_message = f"Echo: {user_message}"  
#         return JsonResponse({"response": response_message})
    
#     return JsonResponse({"error": "Send a POST request with a message"})




# import spacy
# from django.http import JsonResponse
# from rest_framework.decorators import api_view

# nlp = spacy.load("en_core_web_sm")

# intents = {
#     "greeting": ["hello", "hi", "hey"],
#     "bye": ["bye", "goodbye", "see you"],
#     "order": ["order", "buy", "purchase"]
# }

# def classify_intent(text):
#     doc = nlp(text.lower())
#     for token in doc:
#         for intent, keywords in intents.items():
#             if token.text in keywords:
#                 return intent
#     return "unknown"

# @api_view(["POST"])
# def chatbot_response(request):
#     user_message = request.data.get("message", "")
#     intent = classify_intent(user_message)
#     response_message = f"Detected intent: {intent}"
#     return JsonResponse({"response": response_message})


# import json
# import openai
# from django.conf import settings
# from django.http import JsonResponse
# from rest_framework.decorators import api_view
# import os
# from tenacity import retry, wait_random_exponential, stop_after_attempt, wait_fixed
# from fuzzywuzzy import fuzz
# import time
from chatbot.models import Product, Requirement
from django.db import connection
from django.db.models import Q
import re
import nltk, spacy
from nltk.corpus import stopwords
nltk.download('stopwords')

# # Load webscraped data
# with open("C:\Users\mdbl.plc\DjangoApp\mychatbot\chatbot\linked_pages_data.json", "r") as file:
#     bank_data = json.load(file)


# Construct absolute path to your JSON file
# json_path = os.path.join(settings.BASE_DIR, "chatbot", "linked_pages`_data.json")

# # Check if file exists before loading
# if os.path.exists(json_path):
#     with open(json_path, "r", encoding="utf-8") as file:
#         bank_data = json.load(file)
# else:
#     bank_data = {}  # Fallback if file isn't found
#     print(f"Error: File not found at {json_path}")


# def get_relevant_data(query_lower, bank_data):
#     for bank_url, bank_info in bank_data.items():  # Correctly loop over keys and values
#         if any(item.lower() in query_lower for item in bank_info):  # Check against list
#             return {"bank_url": bank_url, "bank_info": bank_info}

#     return None  # No relevant data found


# client = openai.Client(api_key="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")
# @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(5))
# def get_gpt_response(user_message, bank_info=None):
#     system_message = "You are a financial assistant dedicated to providing information about Midland Bank. Only answer queries related to banking, loans, and financial services offered by Midland Bank. If the user's query is unrelated to Midland Bank, politely inform them that you can only provide Midland Bank information."

#     user_prompt = f"User asked: {user_message}"

#     if bank_info:
#         user_prompt = f"User asked: {user_message}\nRelevant Bank Details:\n{json.dumps(bank_info, indent=2)}"
#     else:
#         user_prompt = f"User asked: {user_message}\nNo relevant bank details found."
        

#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": system_message},
#                 {"role": "user", "content": user_prompt}
#             ],
#             max_tokens=100  # Limit response size
#         )
#         return response.choices[0].message.content
#     except openai.OpenAIError as e:
#         print(f"OpenAI API Error: {str(e)}")  # Log error for debugging
#         return "Error: Unable to process request due to API limits."






# def get_gpt_response(user_message, bank_info=None):
#     """ Send user message & retrieved data to GPT for response generation """
#     system_message = "You are a financial assistant. Provide relevant banking information politely."
#     user_prompt = f"User asked: {user_message}"

#     if bank_info:
#         user_prompt += f"\nBank Details:\n{bank_info}"

#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": user_prompt}
#         ],
#         max_tokens=100,  # Reduce token usage
#         temperature=0.7  # Balanced randomness

#     )

#     return response.choices[0].message.content  # Extract response text


# from transformers import pipeline
# from huggingface_hub import login
# login(token="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")

# # Load the model once to improve response speed
# chatbot = pipeline( "text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")

# def get_gpt_response(user_message, bank_info=None):
#     """Generate chatbot responses using Llama 2."""
#     user_prompt = f"User asked: {user_message}"

#     if bank_info:
#         user_prompt += f"\nBank Details:\n{bank_info}"

#     response = chatbot(user_prompt, max_length=200, do_sample=True)
#     return response[0]["generated_text"]  # Extract response text



# List of general banking-related keywords
# bank_keywords = [
#     "midland bank", "loan", "interest rate", "credit card", "accounts",
#     "green banking", "products", "members", "financial statements",
#     "online banking", "deposits", "ATM", "services", "mortgage", "insurance",
#     "transaction", "credit score", "investment", "customer support", "mdb"
# ]

# def is_relevant_query(user_message):
#     """Checks if user query is related to Midland Bank using fuzzy matching."""
#     for keyword in bank_keywords:
#         if fuzz.partial_ratio(user_message.lower(), keyword) > 75:  # Adjust similarity threshold
#             return True
#     return False



# @api_view(["GET","POST"])
# def chatbot_response(request):
#     user_message = request.data.get("message", "").strip().lower()
    
#     if user_message in ["hi", "hello", "hey"]:
#         return JsonResponse({"response": "Hello! How can I help you with Midland Bank today?"})

#     if user_message in ["thank you", "thanks", "thankyou", "thanku", "thank u"]:
#         return JsonResponse({"response": "You are Welcome! Do you need any further asistance?"})

#     if user_message in ["good bye" ,"bye", "Goodbye"]:
#         return JsonResponse({"response": "Bye! Have a great day"})

#     if user_message in ["good morning"]:
#         return JsonResponse({"response": "Good morning!"})
#     if user_message in ["good afternoon"]:
#         return JsonResponse({"response": "Good afternoon!"})
#     if user_message in ["good evening"]:
#         return JsonResponse({"response": "Good evening!"})
    
#      # Use fuzzy matching for flexible query filtering
#     if not is_relevant_query(user_message):
#         return JsonResponse({"response": "I can only provide information about Midland Bank. Please ask a bank-related question."})

#     bank_info = get_relevant_data(user_message.lower(), bank_data)
#     gpt_response = get_gpt_response(user_message, bank_info)

#     return JsonResponse({"response": gpt_response})






# # Construct absolute path to JSON file
# json_path = os.path.join(settings.BASE_DIR, "chatbot", "cleaned_data.json")

# # Load bank data
# if os.path.exists(json_path):
#     with open(json_path, "r", encoding="utf-8") as file:
#         bank_data = json.load(file)
# else:
#     bank_data = {}  # Fallback if file isn't found
#     print(f"Error: File not found at {json_path}")

# # List of general banking-related keywords
# bank_keywords = [
#     "midland bank", "loan", "interest rate", "credit card", "accounts",
#     "green banking", "products", "members", "financial statements",
#     "online banking", "deposits", "ATM", "services", "mortgage", "insurance",
#     "transaction", "credit score", "investment", "customer support", "mdb", "savings", "women", "debit card", "islamic",
    
# ]

# def is_relevant_query(user_message):
#     """Checks if user query is related to Midland Bank using fuzzy matching."""
#     for keyword in bank_keywords:
#         if fuzz.partial_ratio(user_message.lower(), keyword) > 60:  # Adjust similarity threshold
#             return True
#     return False

# def clean_text(text):
#     """Removes excessive whitespace and unnecessary characters."""
#     return text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()

# def get_relevant_data(user_message, bank_data):
#     """Extracts relevant banking information dynamically for any user query."""
#     relevant_info = {}

#     # Common banking categories
#     categories = {
#         "Savings Products": ["savings", "deposit"],
#         "Loan Services": ["loan", "credit", "mortgage"],
#         "General Banking": ["account", "banking", "service"],
#         "Other Financial Services": ["investment", "insurance"],
#         "Women-Focused Services": ["women", "mdb-saalam-sathi"]
#     }

#     # Default to "General Banking" if no match is found
#     query_type = "General Banking"

#     for category, keywords in categories.items():
#         if any(keyword in user_message.lower() for keyword in keywords):
#             query_type = category
#             break

#     # Extract only relevant data based on detected category
#     for bank_url, tags in bank_data.items():
#         for tag, contents in tags.items():
#             for text in contents:
#                 if fuzz.partial_ratio(user_message.lower(), text.lower()) > 80:  # Adjust fuzzy threshold
#                     cleaned_text = clean_text(text)

#                     if query_type not in relevant_info:
#                         relevant_info[query_type] = []

#                     relevant_info[query_type].append(cleaned_text)

#     return relevant_info if relevant_info else None  # Return structured data or None if nothing is found

# client = openai.Client(api_key="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")
# # @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(5))
# # @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
# def get_gpt_response(user_message, bank_info):
#     """Generates a response from OpenAI model using banking-related context."""
    
#       # Determine query category based on keywords
#     if any(keyword in user_message.lower() for keyword in ["savings", "deposit"]):
#         query_type = "Savings Products"
#     elif any(keyword in user_message.lower() for keyword in ["loan", "credit", "mortgage"]):
#         query_type = "Loans & Credit Services"
#     elif any(keyword in user_message.lower() for keyword in ["account", "banking", "services"]):
#         query_type = "General Banking Information"
#     else:
#         query_type = "Other Financial Services"

#     system_message = (
#         "You are an expert financial assistant providing all informations about Midland Bank and its services along with normal banking services. "
#         "Provide a well-organized response focused on {query_type}."
#         "Use the provided banking data in the json file to give precise detailed responses even if the user does not mention a specific bank."
#         "Answer all queries related to banking, loans, and financial services, products, investments, savings "
#         "If the user's query is unrelated, politely inform them that you only provide Midland Bank information."
#     )

#     user_prompt = f"User Query: \"{user_message}\" (Category: {query_type})\n"

#     if bank_info:
#         print(json.dumps(bank_info, indent=4))
        
#         structured_response = ""

#         for page_url, data in bank_info.items():
#             # Include official bank link
#             structured_response += f"\n🔗 **Source:** [{page_url}]({page_url})\n"
#             structured_info = "\n".join(
#             [f"{i+1}. {entry}" for i, entry in enumerate(bank_info.get(query_type.lower(), [])[:5])]
#         )
        
        

        
#         user_prompt += (
#             f"\nRelevant {query_type} Information Extracted:\n"
#             f"{structured_info}\n"
#             f"\nEnsure your response is structured based on this verified bank data."

#         )
#     else:
#         user_prompt += "\nNo relevant bank details found."

#     try:
#         start_time = time.time()
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": system_message},
#                 {"role": "user", "content": user_prompt}
#             ],
#             max_tokens=300,  # Limit response size
#             temperature=0.5
#         )
#         end_time = time.time()

#         print(f"⏳ API Response Time Without Retry: {end_time - start_time} seconds")

#         print(f"✅ OpenAI Response: {response}")  # Debug print
#         return response.choices[0].message.content

#     except openai.OpenAIError as e:
#         print(f"OpenAI API Error: {str(e)}")  # Log error for debugging
#         return "Error: Unable to process request due to API limits or technical issues."

# @api_view(["GET","POST"])
# def chatbot_response(request):
#     """Handles chatbot responses based on user queries."""
#     user_message = request.data.get("message", "").strip().lower()
    
#     if not user_message:  # Handle empty user queries
#         return JsonResponse({"response": "Please enter a valid question about Midland Bank."})

#     # Handle standard greetings
#     greetings = {
#         "hi": "Hello! How can I assist you with Midland Bank today?",
#         "hello": "Hello! How can I assist you with Midland Bank today?",
#         "hey": "Hey there! What banking information do you need?",
#         "thank you": "You're welcome! Let me know if you need further assistance.",
#         "thanks": "You're welcome! Let me know if you need further assistance.",
#         "bye": "Bye! Have a great day!",
#         "goodbye": "Goodbye! Feel free to ask me anytime about Midland Bank.",
#         "good morning": "Good morning! How can I help you with Midland Bank?",
#         "good afternoon": "Good afternoon! What banking services would you like to know about?",
#         "good evening": "Good evening! Do you have any banking-related inquiries?"
#     }
    
#     if user_message in greetings:
#         return JsonResponse({"response": greetings[user_message]})

#     # Use fuzzy matching for flexible query filtering
#     if not is_relevant_query(user_message):
#         return JsonResponse({"response": "I can only provide information about Midland Bank. Please ask a bank-related question."})

#     # Retrieve relevant bank data based on user query
#     bank_info = get_relevant_data(user_message.lower(), bank_data)

#     # Ensure safe handling when no data is found
#     if not bank_info:
#         print("⚠ Warning: No relevant banking data found! Returning basic resp")
#         return JsonResponse({"response": "I couldn't find specific details on your query, but I can still provide general Midland Bank information."})

#     # Get AI-generated response
#     gpt_response = get_gpt_response(user_message, bank_info)

#     return JsonResponse({"response": gpt_response})



#Database base chatbot
# # List of general banking-related keywords
# bank_keywords = [
#     "midland bank", "loan", "interest rate", "credit card", "accounts",
#     "green banking", "products", "financial statements", "online banking",
#     "deposits", "ATM", "services", "mortgage", "insurance", "transaction",
#     "credit score", "investment", "customer support", "mdb", "savings", 
#     "women", "debit card", "islamic",
# ]

# def is_relevant_query(user_message):
#     """Checks if the user query is related to Midland Bank using fuzzy matching."""
#     for keyword in bank_keywords:
#         if fuzz.partial_ratio(user_message.lower(), keyword) > 60:  # Adjust similarity threshold
#             return True
#     return False

# STOPWORDS = {'the', 'is', 'me', 'tell', 'show', 'of', 'all', 'and', 'or', 'about',
#     'list', 'bank', 'info', 'information', 'available', 'midland', 'for', 'what','are', 'features', 
#     'eligibility', 'availability', 'branches', 'available',}

# def fetch_product_info(user_message):
#     """Fetch product details or product names dynamically based on user query intent."""
#     print(f"DEBUG: Received User Query = {user_message}")

#     # Extract keywords
#     user_message_lower = user_message.lower()
#     words = re.findall(r'\w+', user_message_lower)
#     keywords = [word for word in words if word not in STOPWORDS]

#     print(f"DEBUG: Filtered Keywords = {keywords}")

#     if not keywords:
#         return "Please specify what type of product you're looking for (e.g., savings, loan, deposit)."

#     # Check if user is asking about all products
#     generic_keywords = {"products", "available", "midland", "bank"}
#     if all(keyword in generic_keywords for keyword in keywords):
#         products = Product.objects.all().distinct()
#         print("DEBUG: General inquiry detected. Fetching all products.")
#     else:
#         intent_keywords = {"initial", "deposit", "fee", "minimum", "requirement", "document", "need", "is", "what"}
#         product_keywords = [kw for kw in keywords if kw not in intent_keywords]
    
#         query = Q()
#         for keyword in product_keywords:
#             if keyword == "islamic":
#                 query |= Q(IslamicYN="Y")
#             else:
#                 keyword_condition = (
#                     Q(ProductName__icontains=keyword) | 
#                     Q(ProductType__icontains=keyword) | 
#                     Q(Category__icontains=keyword)
#                     )
#                 # AND this with existing query to ensure all keywords must match
#                 query &= keyword_condition
    
#         # Query DB
#         products = Product.objects.filter(query).distinct()
#         print(f"DEBUG: Query Executed = {products.query}")
#         print(f"DEBUG: Retrieved Products = {list(products)}")

#     if not products.exists():
#         return "Sorry, I couldn't find any product matching your query."
    
#     # Check if the user's intent is to ask "Is this Islamic?"
#     if "islamic" in keywords and any(w in user_message_lower for w in ["is", "sharia", "halal"]):
#         if any(p.IslamicYN == "Y" for p in products):
#             islamic_names = ", ".join([p.ProductName for p in products if p.IslamicYN == "Y"])
#             return f"Yes, Midland Bank offers Islamic products matching your query: {islamic_names}."
#         else:
#             names = ", ".join([p.ProductName for p in products])
#             return f"The following products matched your query but are not Islamic: {names}."


#     # Determine if the user asked for "names only" (e.g. list, show, tell, products)
#     only_show_names = True
#     detail_keywords = {"detail", "requirements", "need", "document", "info", "information",
#     "explain", "features", "deposit", "fee", "initial", "minimum", 'eligibility','availability'}

#     if any(word in detail_keywords for word in words):
#         only_show_names = False

#     if only_show_names:
#         product_names = "\n".join([f"- {product.ProductName}" for product in products])
#         return f"**📋 Available Products:**\n{product_names}"

#     # If user wants details
#     response_data = []
#     for product in products:
#         requirements = Requirement.objects.filter(ProductCode=product.ProductCode)

#        # Extract fee (initial deposit)
#     initial_deposit_req = requirements.filter(DocumentType__iexact="Fees").first()
#     initial_deposit = initial_deposit_req.DocumentName if initial_deposit_req else "Not Specified"
#     print({initial_deposit})
#     # Get other requirements (excluding Fees)
#     document_reqs = requirements.exclude(DocumentType__iexact="Fees")
#     requirement_list = "\n".join([
#         f"- {req.DocumentName} ({req.DocumentType})"
#         for req in document_reqs
#     ]) or "Not Specified"
    
#     response_data.append(f"""  
#     **🏦 {product.ProductName}**  
#     - **Type:** {product.ProductType}  
#     - **Category:** {product.Category}  
#     - **Islamic Banking:** {"Yes" if product.IslamicYN == "Y" else "No"}  
#     - **Minimum Initial Deposit:** {initial_deposit}  
#     - **Required Documents:**  
#       {requirement_list}  
#     """)


#     return "\n\n".join(response_data)



# client = openai.Client(api_key="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")
# def get_gpt_response(user_message, product_info):
#     """Generate response using OpenAI API with contextual banking data."""
#     system_message = (
#         "You are an expert financial assistant providing detailed information "
#         "about Midland Bank and its banking services. Answer queries in a structured "
#         "point-based format, ensuring clarity. Only use relevant banking data from the database"
#         "to give precise detailed responses even if the user does not mention a specific bank."
#         "Answer all queries related to banking, loans, and financial services, products, investments, savings of Midland Bank"
#         "If asked about products, list, or names just give the name of the products do not give details if not asked something like details, features or description of the product"
#         "If the user's query is unrelated, politely inform them that you only provide Midland Bank information."
#     )

#     user_prompt = f"User Query: \"{user_message}\"\n\n"

#     if product_info:
#         user_prompt += (
#             "**Relevant Banking Product Information:**\n\n"
#             f"{product_info}\n\n"
#             "Ensure your response is structured in points."
#         )
#     else:
#         user_prompt += "\nNo relevant bank details found."

#     try:
#         start_time = time.time()
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": system_message},
#                 {"role": "user", "content": user_prompt}
#             ],
#             max_tokens=300,
#             temperature=0.5
#         )
#         end_time = time.time()

#         print(f"⏳ API Response Time: {end_time - start_time} seconds")
#         return response.choices[0].message.content

#     except openai.OpenAIError as e:
#         print(f"OpenAI API Error: {str(e)}")
#         return "Error: Unable to process request due to API limits or technical issues."

# @api_view(["GET", "POST"])
# def chatbot_response(request):
#     """Handles chatbot responses dynamically using MySQL-based banking data."""
#     user_message = request.data.get("message", "").strip().lower()

#     if not user_message:
#         return JsonResponse({"response": "Please enter a valid question about Midland Bank."})

#     # Handle standard greetings
#     greetings = {
#         "hi": "Hello! How can I assist you with Midland Bank today?",
#         "hello": "Hello! How can I assist you with Midland Bank today?",
#         "hey": "Hey there! What banking information do you need?",
#         "thank you": "You're welcome! Let me know if you need further assistance.",
#         "thanks": "You're welcome! Let me know if you need further assistance.",
#         "bye": "Bye! Have a great day!",
#         "goodbye": "Goodbye! Feel free to ask me anytime about Midland Bank.",
#         "good morning": "Good morning! How can I help you with Midland Bank?",
#         "good afternoon": "Good afternoon! What banking services would you like to know about?",
#         "good evening": "Good evening! Do you have any banking-related inquiries?"
#     }
    
#     if user_message in greetings:
#         return JsonResponse({"response": greetings[user_message]})

#     # Use fuzzy matching for flexible query filtering
#     if not is_relevant_query(user_message):
#         return JsonResponse({"response": "I can only provide information about Midland Bank. Please ask a bank-related question."})

#     # Fetch relevant banking product details dynamically from MySQL
#     product_info = fetch_product_info(user_message)
    
#     print(f"DEBUG: Fetched Product Info = {product_info}")  # Debug print
#     print(connection.settings_dict["NAME"]) 

#     if product_info:
#         return JsonResponse({"response": get_gpt_response(user_message, product_info)})

#     return JsonResponse({"response": "I couldn't find details on that product, but I can provide general Midland Bank information."})



#chroma db base chatbot

# ChromaDB based chatbot implementation
import json
import openai
from openai import OpenAI
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
import os
from tenacity import retry, wait_random_exponential, stop_after_attempt
import chromadb
from chromadb.config import Settings
from fuzzywuzzy import fuzz
import time, re
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress INFO and WARNING logs
import diskcache as dc
cache = dc.Cache("cache_dir")  # Initialize disk cache for caching results
from chromadb.utils import embedding_functions
# Import the loaded product aliases data
from chatbot.apps import product_aliases_data as product_aliases

# embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="BAAI/bge-base-en-v1.5"
# )

# # Initialize ChromaDB client
# chroma_client = chromadb.PersistentClient(
#     path=r"C:\Users\mdbl.plc\Scraper\chroma_rich",
#     settings=Settings(
#         anonymized_telemetry=False  # Disable telemetry for faster performance
#     )
# )

# collection = chroma_client.get_collection(
#     name="midland_detailed",
#     embedding_function=embedding_func
# )

# # List of banking-related keywords for query filtering
# bank_keywords = [
#     "midland bank", "loan", "interest rate", "credit card", "accounts",
#     "green banking", "products", "financial statements", "online banking",
#     "deposits", "ATM", "services", "mortgage", "insurance", "transaction",
#     "credit score", "investment", "customer support", "mdb", "savings", 
#     "women", "debit card", "islamic", "branch", "location", "contact",
#     "schedule", "working hours", "mobile banking", "internet banking",
#     "corporate", "sme", "retail", "agent banking", 'bank', 'family support', 'midland online', 'midland app',
#     'midland bank app', 'midland online banking', 'midland mobile banking', 'jhotpot', 'achallan', 'amar bari'
# ]


# def is_relevant_query(user_message):
#     """Check if query is banking-related using fuzzy matching."""
#     for keyword in bank_keywords:
#         if fuzz.partial_ratio(user_message.lower(), keyword) > 60:
#             return True
#     return False

# @retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(2))
# def get_relevant_chroma_data(query: str, n_results: int = 5):
#     cache_key = f"chroma:{query.lower().strip()}"
#     if cache_key in cache:
#         print("⚡ Serving ChromaDB result from cache")
#         return cache[cache_key]

#     # Define comprehensive category keywords for better matching
#     category_keywords = {
#         'management': {
#             'keywords': ['chairman', 'managing director', 'ceo', 'board', 'director', 'management', 'head', 'chief', 'executive', 'leadership', 'cto', 'md'],
#             'weight': 1.5,
#             'exclusive': True
#         },
#         'location': {
#             'keywords': ['head office', 'branch', 'location', 'address', 'tower', 'gulshan', 'dhaka', 'contact', 'email', 'phone', 'fax','N.B', 'address of', 'where is', 'what is the address of'],
#             'weight': 1.5,
#             'exclusive': True
#         },
#         'general_banking': {
#             'keywords': ['account', 'banking', 'service', 'facility', 'scheme', 'transaction', 'branch'],
#             'weight': 1.2,
#             'exclusive': False
#         },
#         'loans': {
#             'keywords': ['loan', 'credit', 'mortgage', 'financing', 'interest rate', 'tenure', 'emi'],
#             'weight': 1.2,
#             'exclusive': False
#         },
#         'cards': {
#             'keywords': ['card', 'credit card', 'debit card', 'prepaid', 'visa', 'mastercard'],
#             'weight': 1.2,
#             'exclusive': False
#         },
#         'islamic': {
#             'keywords': ['islamic', 'saalam', 'shariah', 'mudaraba', 'murabaha', 'halal'],
#             'weight': 1.5,
#             'exclusive': True
#         },
#         'savings': {
#             'keywords': ["savings", "deposit", "dps", "super saver", "school saver", "college saver", "cpp savings",
#                          "gift cheque", "kotipoti", "millionaire", "platinum savings", "traveller's savings",
#                          "e-saver", "interest first", "personal retail account", "sathi", "super high performance",
#                          "digital savings", "family support", "double benefit"],
#             'weight': 1.5,
#             'exclude_terms': ['islamic', 'shariah', 'mudaraba'],
#             'exclusive': True
#         },
#         'digital': {
#             'keywords': ['digital', 'online', 'internet banking', 'mobile banking', 'app', 'electronic'],
#             'weight': 1.2,
#             'exclusive': False
#         },
#         'features': {
#             'keywords': ['feature', 'benefit', 'eligibility', 'requirement', 'document', 'criteria'],
#             'weight': 1.1,
#             'exclusive': False
#         },
#         'corporate': {
#             'keywords': ['corporate', 'business', 'enterprise', 'company', 'commercial', 'merchant'],
#             'weight': 1.2,
#             'exclusive': False
#         }
#     }
    
    
#     def identify_query_category(query):
#         """Identify the primary category of the query."""
#         query_lower = query.lower()
#         category_scores = {}
#         for category, info in category_keywords.items():
#             score = 0
#             for keyword in info['keywords']:
#                 if re.search(rf'\b{re.escape(keyword.lower())}\b', query_lower):
#                     score += 1
#             if score > 0:
#                 category_scores[category] = score * info['weight']
#         if not category_scores:
#             return None, 0
#         primary_category = max(category_scores.items(), key=lambda x: x[1])
#         return primary_category[0], primary_category[1]

#     def calculate_relevance_score(doc, query, found_categories, query_category, product_aliases, meta=None, distance=0.0): # Added product_aliases, meta
#         """
#         Calculate a weighted relevance score for a document with category focus,
#         generality penalty, and service-specific boosts.
#         """
#         query_lower = query.lower()
#         doc_lower = doc.lower()
#         query_terms = set(query_lower.split())
#         doc_terms = set(doc_lower.split())

#         term_overlap = len(query_terms.intersection(doc_terms))

#         # --- Category Weight Calculation ---
#         is_general_query = bool(re.match(r"what is\s+(.*?)\??$", query_lower))

#         if query_category and category_keywords[query_category]['exclusive']:
#             if query_category in found_categories:
#                 category_weight = 2.0
#             else:
#                 category_weight = 0.3
#         else:
#             # For non-exclusive categories, give a stronger boost if the query's primary category is found
#             if query_category in found_categories:
#                 base_category_score = sum(category_keywords[cat]['weight'] for cat in found_categories)
#                 if is_general_query:
#                     category_weight = base_category_score * 1.5 # Stronger boost for general queries
#                 else:
#                     category_weight = base_category_score * 1.2 # Regular boost
#             else:
#                 category_weight = sum(category_keywords[cat]['weight'] for cat in found_categories) if found_categories else 1.0

#         # Check for exact phrase matches
#         exact_matches = sum(1 for phrase in query_terms if phrase in doc_lower)

#         # Calculate proximity score
#         proximity_score = 0.0 # Initialize to 0.0, will be calculated if applicable
#         if len(query_terms) > 1:
#             words = doc_lower.split()
#             positions = {}
#             for i, word in enumerate(words):
#                 for term in query_terms:
#                     if term in word:
#                         if term not in positions:
#                             positions[term] = []
#                         positions[term].append(i)

#             if len(positions) > 1:
#                 min_distance = float('inf')
#                 for term1_key in positions:
#                     for term2_key in positions:
#                         if term1_key != term2_key:
#                             for pos1 in positions[term1_key]:
#                                 for pos2 in positions[term2_key]:
#                                     distance = abs(pos1 - pos2)
#                                     min_distance = min(min_distance, distance)
#                 if min_distance != float('inf'):
#                     proximity_score = 1.0 / (1.0 + min_distance)
#                 else:
#                     proximity_score = 0.25 # If terms are found but too far apart or not forming a cluster

#         # Initial final score components
#         final_score = (
#             (term_overlap * 0.25) +
#             (exact_matches * 0.25) +
#             (proximity_score * 0.2) +
#             (category_weight * 0.3)
#         )
        
#         product_match_boost_applied = False
#         for alias_key, canonical_name in product_aliases.items():
#             # Check if the query contains the alias key (e.g., "jhotpot" or "gift cheque")
#             if alias_key.lower() in query_lower:
#                 # If found in query, check if the document content contains the canonical name
#                 # or the alias itself (case-insensitive and as a whole word if possible)
#                 if re.search(r'\b' + re.escape(canonical_name.lower()) + r'\b', doc_lower) or \
#                    re.search(r'\b' + re.escape(alias_key.lower()) + r'\b', doc_lower):
#                     final_score += 200.0 # <--- Give a very large, decisive boost! Adjust this value if needed (e.g., 500.0)
#                     product_match_boost_applied = True
#                     break # Apply only once if multiple aliases match the same doc

#         # Additionally, if the exact query text (or a significant portion) matches a product name, give a boost
#         # This captures cases like "what is jhotpot" where "jhotpot" is the product.
#         for canonical_name in set(product_aliases.values()): # Use canonical names for broader matching
#             if re.search(r'\b' + re.escape(canonical_name.lower()) + r'\b', query_lower) and \
#                re.search(r'\b' + re.escape(canonical_name.lower()) + r'\b', doc_lower):
#                 if not product_match_boost_applied: # Avoid double boosting for the same product
#                     final_score += 150.0 # Slightly less than direct alias match, but still strong
#                     product_match_boost_applied = True
#                 break # Apply only once

#         # Consider a specific boost if the title in meta contains the queried product
#         # Ensure meta is not None before accessing it
#         if meta and 'title' in meta:
#             title_lower = meta['title'].lower()
#             for alias_key, canonical_name in product_aliases.items():
#                 if (alias_key.lower() in query_lower or canonical_name.lower() in query_lower) and \
#                    (alias_key.lower() in title_lower or canonical_name.lower() in title_lower):
#                     final_score += 50.0 # Additional boost for title match
#                     break # Apply only once

#         # --- Generality Penalty for Product-Specific Content ---
#         if is_general_query and query_category == 'digital': # Apply specifically for digital, or other general categories
#             specific_product_mentions = 0
#             canonical_product_names = set(product_aliases.values())

#             for p_name in canonical_product_names:
#                 if re.search(rf'\b{re.escape(p_name.lower())}\b', doc_lower):
#                     specific_product_mentions += 1

#             if specific_product_mentions >= 3:
#                 final_score *= 0.5 # Substantial penalty
#             elif specific_product_mentions >= 1:
#                 final_score *= 0.8 # Moderate penalty

#         # --- Service-Specific Query Boost ---
#         if any(k in query_lower for k in ["services", "what services", "list services", "service provided", "what are the services", "features of agent banking"]):
#             explicit_service_phrases_in_doc = 0

#             explicit_service_phrases_patterns = [
#                 r"what is midland online"
#                 r"services available",
#                 r"key services",
#                 r"list of services",
#                 r"special features of mdb agent banking",
#                 r"prohibited activities",
#                 r"features of agent banking",
#                 r"services provided by agent banking"
#             ]

#             for pattern in explicit_service_phrases_patterns:
#                 if re.search(pattern, doc_lower):
#                     explicit_service_phrases_in_doc += 1

#             if explicit_service_phrases_in_doc > 0:
#                 final_score += (explicit_service_phrases_in_doc * 1.0)

#             if "prohibited" in query_lower and "prohibited activities" in doc_lower:
#                 final_score += 1.5

#         # --- Optional: Title/Heading Boost (Requires 'meta' to be passed and contain 'title') ---
#         if meta and 'title' in meta:
#             title_lower = meta['title'].lower()
#             if any(k in query_lower for k in ["services", "features"]) and \
#                ("services available" in title_lower or "special features" in title_lower or "prohibited activities" in title_lower):
#                 final_score += 1.0

#         # ✨ Bonus weight for known role patterns
#         bonus_keywords = {
#             "managing director": 0.8, "deputy managing director": 0.8, "dmd":0.8,
#             "chief risk officer": 0.5, "chief technology officer": 0.5, "ahsan-uz zaman": 0.8,
#             "zahid hossain": 0.8, "ceo":0.8, "md":0.8, "md. nazmul huda sarkar": 0.8,
#             "cto":0.8, "chairman": 1.0, "ahsan khan chowdhury": 1.0,
#         }
#         for kw, bonus in bonus_keywords.items():
#             if kw in doc_lower:
#                 final_score += bonus
                
#         semantic_score_from_distance = (1 - (distance / 2.0)) * 5.0 # Give it a moderate weight
#         final_score += semantic_score_from_distance

#         # Ensure score doesn't become negative (good practice)
#         if final_score < 0:
#             final_score = 0        

#         return final_score

#     try:
#         print(f"\n📦 Querying vector data from ChromaDB collection: {collection.name}")
#         results = collection.query(
#             query_texts=[query],
#             n_results=n_results * 5,
#             include=["documents", "metadatas", "distances"]
#         )

#         all_results = []
#         query_category, query_category_score = identify_query_category(query)
#         print(f"\nIdentified query category: {query_category} (score: {query_category_score:.2f})")

#         if results and results['documents']:
#             for idx, doc in enumerate(results['documents'][0]):
#                 meta = results['metadatas'][0][idx]
#                 dist = results['distances'][0][idx]
#                 # Find matching categories
#                 found_categories = []
#                 for category, info in category_keywords.items():
#                     if any(kw.lower() in doc.lower() for kw in info['keywords']):
#                         found_categories.append(category)
#                 # Calculate relevance score with category focus
#                 relevance_score = calculate_relevance_score(doc, query, found_categories, query_category, product_aliases, meta, dist)
#                 # Only include results that match the query category if it's exclusive
#                 if query_category and category_keywords[query_category].get('exclusive', False):
#                     if query_category not in found_categories and not any(
#                         kw in doc.lower() for kw in ['savings', 'account', 'deposit', 'scheme']):
#                         continue
#                 result_entry = {
#                     'content': doc,
#                     'score': dist,
#                     'collection': collection.name,
#                     'categories': found_categories,
#                     'relevance_score': relevance_score
#                 }
#                 all_results.append(result_entry)

#         # Sort results using the comprehensive scoring system
#         all_results.sort(key=lambda x: x['relevance_score'], reverse=True)

#         # Filter results to keep only the most relevant ones
#         if query_category and category_keywords[query_category].get('exclusive', False):
#             best_results = [r for r in all_results[:n_results] if query_category in r['categories']]
#         else:
#             best_results = all_results[:n_results]

#         if best_results:
#             formatted_results = []
#             for result in best_results:
#                 # For exclusive categories, only show the relevant part of the content
#                 if query_category == "location":
#                     if any(key in result['content'].lower() for key in ["gulshan", "n. b. tower", "40/7", "dhaka"]):
#                         content = result['content']
#                     else:
#                         content = (
#                             "Midland Bank Limited Head Office:\n"
#                             "N. B. Tower (Level 6–9)\n"
#                             "40/7 Gulshan Avenue\n"
#                             "Gulshan-2, Dhaka-1212, Bangladesh."
#                              )
#                 elif query_category and category_keywords[query_category]['exclusive']:
#                     sentences = result['content'].split('.')
#                     relevant_sentences = []
#                     query_terms = set(query.lower().split())
#                     for sentence in sentences:
#                         if any(term in sentence.lower() for term in query_terms):
#                             relevant_sentences.append(sentence)
#                     if relevant_sentences:
#                         content = '. '.join(relevant_sentences) + '.'
#                     else:
#                         content = result['content']
#                 else:
#                     content = result['content']
#                 formatted_results.append(f"• {content}\n  [Relevance: {result['relevance_score']:.4f}]")

#             # Debug log each document being passed to GPT
#             print("\n📄 Documents sent to GPT:")
#             for result in best_results:
#                 print(f"\n[Collection: {result['collection']}]")
#                 print(f"Categories: {result['categories']}")
#                 print(f"Relevance Score: {result['relevance_score']:.4f}")
#                 print("Content Preview:\n", result['content'][:500], "...\n")

#             # ✅ Return raw results instead of formatted preview
#             raw_results = [result['content'].strip() for result in best_results]
#             context = "\n\n".join(raw_results)
#             cache[cache_key] = context
#             return context


#         return "No relevant information found in the bank's knowledge base."

#     except Exception as e:
#         print(f"ChromaDB Error: {str(e)}")
#         return "Error accessing the knowledge base."
        
# # Initialize OpenAI client
# client = OpenAI(api_key=settings.API_KEY)

# def clean_response(text):
#     """Remove forbidden starting phrases and sentences mentioning 'context'."""
#     forbidden_starts = [
#         r"(?i)^(based on|according to|as per|given the|from the information|it appears|looking at|the context).*"
#     ]
#     lines = text.split('\n')
#     clean_lines = [line for line in lines if not any(re.match(p, line.strip()) for p in forbidden_starts)]
#     # Remove sentences containing the word 'context'
#     clean_text = []
#     for line in clean_lines:
#         sentences = line.split('.')
#         filtered_sents = [s for s in sentences if "context" not in s.lower()]
#         clean_text.append('.'.join(filtered_sents).strip())
#     return "\n".join(clean_text).strip()


# def get_gpt_response(user_message: str, context: str) -> str:
#     cache_key = f"gpt:{hash(user_message + context)}"
#     if cache_key in cache:
#         print("⚡ GPT response from cache")
#         return cache[cache_key]
    
#     system_message = """You are an expert financial assistant for Midland Bank. Answer user questions clearly, concisely, and politely, using only the provided bank data.

#     Here are your strict rules:
    
#     1.  **Source Adherence:** Only use information provided in the bank data. Do not make up, infer, or add external information. If something is not in the bank data, politely state that the information is not found.
#     2.  **Directness & Conciseness:** Respond directly and concisely to the question. Aim to provide all relevant details from the provided bank data that directly answer the query, without unnecessary elaboration.
#     3.  **No Explanations/Filler:** Do NOT explain your reasoning, offer conversational filler, or use phrases like "Given the context", "According to the documents", "Based on the information", "From the context", "I can tell you that...", or similar.
#     4.  **No Source Attribution:** Never mention sources, documents, or data.
#     5.  **Personnel/Management Queries:**
#         * State only the name and their specific position (e.g., CEO, Chairman).
#         * Never infer titles or positions. Only respond if both the name and their *exact* title appear directly in the provided information.
#         * Do not guess. If the role is not clearly stated, respond with: 'Not found.'
#         * Do NOT use bullet points or lists for this info.
#     6.  **Location or Contact Info:**
#         * Provide only the address or contact details. No extra context or introductory phrases.
#     7.  **Product List Queries (General or Category-Specific):**
#         * If the user asks for a list of all products or products within a category (e.g., "all products", "list of products", "Islamic products", "savings products", "are there any X products?"), begin your answer with a short, polite introductory sentence like "Midland Bank offers the following products:" or "Yes, Midland Bank offers these Islamic products:".
#         * After the introduction, provide a clear bullet-point list of product names only.
#         * Do NOT provide descriptions or features unless specifically asked.
#     8.  **Specific Product Queries:**
#         * If the user asks about a **specific product**, provide only relevant information for that product.
#     9.  **Product/Service Definitions:**
#         * **If the user asks for a definition of a specific product or service (e.g., "what is X?", "define Y"), provide a concise summary of its purpose or what it does, directly from the available data. Do not use bullet points for definitions unless the definition itself is naturally structured as a list in the source.**
#     10. **Services or Features Queries:**
#         * If asked about **services** (e.g., "services offered by Agent Banking") or **features of a specific product** (e.g., "what are the features of X?"), start with a single, concise introductory sentence identifying the subject (e.g., "The services offered by Agent Banking include:" or "Features of X include:").
#         * Follow this introduction with available information using clear bullet points, including:
#             * Minimum deposit or amount
#             * Tenure (duration)
#             * Eligibility
#             * Features/Benefits
#             * Documents required
#             * Interest or profit rate
#             * Loan facilities (if any)
#             * Any other important field
#         * Only provide information that is explicitly stated in the provided context.
#     11. **General Queries:**
#         * For all other queries, respond clearly and concisely. Use bullet points only when listing multiple distinct items.

#     """
    
#     try:
#         messages =[
#             {"role": "system", "content": system_message}, 
#         ]
#         if context:
#             messages.append({"role": "assistant", "content": context})

#         # Then user question:
#         messages.append({"role": "user", "content": user_message})
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=messages,
#             max_tokens=800,
#             temperature=0.7
#         )
        
#         gpt_response = response.choices[0].message.content
#         cleaned_response = clean_response(gpt_response)
        
#         # Store in cache if needed
#         cache[cache_key] = cleaned_response
        
#         return cleaned_response 
        
#     except Exception as e:
#         print(f"OpenAI API Error: {str(e)}")
#         return "I apologize, but I'm having trouble processing your request at the moment. Please try again."


# def truncate_context(context, max_chars=6000):
#     if len(context) <= max_chars:
#         return context
#     truncated = context[:max_chars]
#     last_period = truncated.rfind('.')
#     if last_period == -1 or last_period < max_chars * 0.5:
#         return truncated.strip() + " ..."
#     return truncated[:last_period+1]

# def deduplicate_lines(text):
#     seen = set()
#     deduped = []
#     for line in text.splitlines():
#         line = line.strip()
#         if line and line not in seen:
#             deduped.append(line)
#             seen.add(line)
#     return "\n".join(deduped)

# @api_view(["GET", "POST"])
# def chatbot_response(request):
#     """Handle chatbot responses using ChromaDB and GPT."""
#     user_message = request.data.get("message", "").strip()
    
#     if not user_message:
#         return JsonResponse({"response": "Please enter a question about Midland Bank."})

#     # Handle common greetings
#     greetings = {
#         "hi": "Hello! How can I assist you with Midland Bank today?",
#         "hello": "Hello! How can I assist you with Midland Bank today?",
#         "hey": "Hey there! What banking information do you need?",
#         "thank you": "You're welcome! Let me know if you need further assistance.",
#         "thanks": "You're welcome! Let me know if you need further assistance.",
#         "bye": "Bye! Have a great day!",
#         "goodbye": "Goodbye! Feel free to ask me anytime about Midland Bank.",
#         "good morning": "Good morning! How can I help you with Midland Bank?",
#         "good afternoon": "Good afternoon! What banking services would you like to know about?",
#         "good evening": "Good evening! Do you have any banking-related inquiries?",
#         "okay": "Do you need any further assistance?",
#         "ok": "Do you need any further assistance?"
#     }

#     user_message_lower = user_message.lower()
    
#     for alias, canonical in product_aliases.items():
#         if alias in user_message_lower:
#             print(f"🔁 Normalizing '{alias}' to '{canonical}'")
#             user_message_lower = user_message_lower.replace(alias, canonical)
#             user_message = user_message.replace(alias, canonical)

    
#     role_aliases = {
#     "chief technology officer": "cto",
#     "deputy managing director": "dmd",
#     "chief risk officer": "cro",
#     "chief executive officer": "ceo", 
#     "managing director": "md"
#      }

#     for phrase, alias in role_aliases.items():
#         user_message_lower = user_message_lower.replace(phrase, alias)
        
#     if user_message_lower in greetings:
#         return JsonResponse({"response": greetings[user_message_lower]})

#     # Check if query is banking-related
#     if not is_relevant_query(user_message):
#         return JsonResponse({
#             "response": "I can only provide information about Midland Bank. Please ask a bank-related question."
#         })
        
        
#     # === New: Structured product list handling ===
#     general_product_queries = [
#         "list products", "all products", "product categories",
#         "what products do you have", "show all products", "what are the products", "available products",
#         "product list", "products offered", "product categories list", "product names", "list of products",
#         "what products are available", "list of midland bank products", "midland bank products",
#         "midland bank product list", "midland bank product categories"
#     ]
    
#     if any(q in user_message_lower for q in general_product_queries):
#         grouped = list_products_grouped_by_category()
#         if not grouped:
#             return JsonResponse({"response": "No products found in the knowledge base."})
    
#         response = []
#         response.append("Midland Bank offers the following products:")
#         for cat, products in sorted(grouped.items()):
#             response.append(f"**{cat} Products**")
#             response.extend(f"- {p}" for p in products)
#             response.append("")  # spacing
#         return JsonResponse({"response": "\n".join(response)})
    
#     category_map = {
#         "savings": ["savings", "saving accounts", "dps"],
#         "loans": ["loan", "loans"],
#         "cards": ["card", "visa", "debit", "prepaid", "credit card"],
#         "islamic": ["islamic", "shariah", "saalam"]
#     }
    
#     for cat, triggers in category_map.items():
#         if any(k in user_message_lower for k in triggers) and "product" in user_message_lower:
#             products = list_products_by_category(cat)
#             if products:
#                 return JsonResponse({"response": "\n".join(f"- {p}" for p in products)})
#             else:
#                 return JsonResponse({"response": f"No {cat} products found."})
        
    
        
#     # Get relevant information from ChromaDB
#     print(f"🔍 Processing query: {user_message}")
#     start_time = time.time()
#     context = get_relevant_chroma_data(user_message)
#     print(f"DEBUG: Context directly from get_relevant_chroma_data (first 500 chars):\n{context[:500]}")
#     print(f"DEBUG: Type of context: {type(context)}")
#     if isinstance(context, list):
#         context = "\n\n".join(c["content"].strip() for c in context if "content" in c)
#     end_time = time.time()
#     print(f"⏳ ChromaDB Query Time: {end_time - start_time:.2f} seconds")
#     inspect_chroma_collections()
        
#     # Management roles to look for
#     management_roles = [
#         "managing director", "ceo", "chairman", "cto", "chief technology officer",
#         "chief risk officer", "deputy managing director", "md", "dmd"
#     ]
    
#     # If the query is about management, extract only relevant lines
#     if any(role in user_message_lower for role in management_roles):
#         context = extract_management_sentences(context, management_roles)
    
    
#     # Generate response using GPT
#     context = context or ""
#     print("gpt context", context[:800])  # Debug print to check context length
#     # context = deduplicate_lines(context)
#     context = truncate_context(context) 
    
#     # 🔥 Add GPT cache check here
#     gpt_cache_key = f"gpt:{hash(user_message + context)}"
#     if gpt_cache_key in cache:
#         print("⚡ Serving GPT reply from cache")
#         return JsonResponse({"response": cache[gpt_cache_key]})
    
#     response = get_gpt_response(user_message, context)
#     print(f"🤖 GPT Response: {response}")
#     return JsonResponse({"response": response})       

# @api_view(["GET"])
# def list_products(request):
#     products = list_products_grouped_by_category()
#     return JsonResponse({"products": products})

# # After ChromaDB client initialization
# def inspect_chroma_collections():
#     """Inspect ChromaDB collections and their metadata"""
#     try:
#         collections = [collection]
#         print("\n=== ChromaDB Collections Information ===")
#         for coll in collections:
#             print(f"\nCollection Name: {collection.name}")
#             print(f"Number of documents: {collection.count()}")
#             # Get collection metadata if any
#             try:
#                 peek = collection.peek()
#                 if peek and peek['documents']:
#                     print("Sample document:", peek['documents'][0][:200], "...")
#             except Exception as e:
#                 print(f"Error peeking collection: {str(e)}")
#     except Exception as e:
#         print(f"Error inspecting collections: {str(e)}")


# def list_products_grouped_by_category():
#     """Group all products by category using ChromaDB metadata."""
#     try:
#         data = collection.get(include=["metadatas"])
#         grouped = {}
#         for meta in data["metadatas"]:
#             title = meta.get("title", "").strip()
#             category = meta.get("category", "general").strip().title()
#             if title and "MDB" in title:
#                 cleaned_title = clean_title(title)
#                 grouped.setdefault(category, set()).add(cleaned_title)
#         return {k: sorted(v) for k, v in grouped.items()}
#     except Exception as e:
#         print(f"Error grouping products: {e}")
#         return {}

# def clean_title(title):
#     return title.replace("– Midland Bank PLC.", "").strip()

# def list_products_by_category(category):
#     grouped = list_products_grouped_by_category()
#     return sorted(list(grouped.get(category.title(), [])))


# def extract_management_sentences(context, role_keywords):
#     """Extract sentences mentioning management roles from the context."""
#     sentences = re.split(r'(?<=[.?!])\s+', context.strip())
#     relevant = []
#     for sentence in sentences:
#         if any(re.search(rf'\b{re.escape(role)}\b', sentence, re.IGNORECASE) for role in role_keywords):
#             relevant.append(sentence.strip())
#     return "\n".join(relevant)



# Import from your new modules
from chatbot.data import config # Your new config file
from chatbot.services import retrieval_services
from chatbot.services.retrieval_services import identify_query_category
from chatbot.services import llm_services
from chatbot.services import product_listing_service
from chatbot.utils import text_utils



# Load product aliases (adjust path if it's not in chatbot_app/data/)
try:
    with open('chatbot/data/product_aliases.json', 'r', encoding='utf-8') as f:
        PRODUCT_ALIASES = json.load(f)
except FileNotFoundError:
    print("WARNING: product_aliases.json not found. Alias normalization might be limited.")
    PRODUCT_ALIASES = {}


@api_view(["GET", "POST"])
def chatbot_response(request):
    """Handle chatbot responses using ChromaDB and GPT."""
    user_message = request.data.get("message", "").strip()
    
    if not user_message:
        return JsonResponse({"response": "Please enter a question about Midland Bank."})

    user_message_lower = user_message.lower()
    query_category_identified, _ = identify_query_category(user_message)
    print(f"DEBUG: Identified Query Category: {query_category_identified}")
    
    
    # Apply role aliases first for common phrase standardization
    for phrase, alias in config.role_aliases.items():
        user_message_lower = user_message_lower.replace(phrase, alias)
        user_message = user_message.replace(phrase, alias) # Apply to original message too if needed for later use
    
    # Apply product/general aliases for query normalization
    for alias, canonical in PRODUCT_ALIASES.items():
        alias_pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
        if alias_pattern.search(user_message): 
            print(f"🔁 Normalizing '{alias}' to '{canonical}'")
            user_message_lower = alias_pattern.sub(canonical.lower(), user_message_lower)
            user_message = alias_pattern.sub(canonical, user_message)
        


    # Handle common greetings
    if user_message_lower in config.greetings:
        return JsonResponse({"response": config.greetings[user_message_lower]})

    # Check if query is banking-related
    if not text_utils.is_relevant_query(user_message):
        return JsonResponse({
            "response": "I can only provide information about Midland Bank. Please ask a bank-related question."
        })
        
    # === Structured product list handling ===
    if any(q in user_message_lower for q in config.general_product_queries):
        grouped = product_listing_service.list_products_grouped_by_category()
        if not grouped:
            return JsonResponse({"response": "No products found in the knowledge base."})
        
        response_lines = []
        response_lines.append("Midland Bank offers the following products:")
        for cat, products in sorted(grouped.items()):
            response_lines.append(f"**{cat} Products**")
            response_lines.extend(f"- {p}" for p in products)
            response_lines.append("")  # spacing
        return JsonResponse({"response": "\n".join(response_lines)})
    
    # Category-specific product listing
    for cat, triggers in config.category_map.items():
        if any(k in user_message_lower for k in triggers) and "product" in user_message_lower:
            products = product_listing_service.list_products_by_category(cat)
            if products:
                return JsonResponse({"response": "\n".join(f"- {p}" for p in products)})
            else:
                return JsonResponse({"response": f"No {cat} products found."})
        
    # Get relevant information from ChromaDB
    print(f"🔍 Processing query: {user_message}")
    start_time = time.time()
    # Pass all necessary config data to the service function
    raw_context = retrieval_services.get_relevant_chroma_data(user_message)
    print("DEBUG: Raw context type: ", raw_context[:300])
    context = raw_context
    end_time = time.time()
    print(f"⏳ ChromaDB Query Time: {end_time - start_time:.2f} seconds")
    print("DEBUG: Context directly from get_relevant_chroma_data (first 500 chars):\n", context[:300])
    # retrieval_service.inspect_chroma_collections() 
    
    # If the query is about board members, extract relevant lines
    if query_category_identified== 'board':
        board_context = text_utils.extract_board_sentences(context)
        if board_context.strip():
            formatted_board_context = "\n".join([
            f"• {line.strip()}" for line in board_context.splitlines()
            ])
            context = formatted_board_context
            print("DEBUG: Extracted board context (first 300 chars):\n", context[:300])
            
    # If the query is about management, extract only relevant lines
    elif query_category_identified == 'management':
        management_context = text_utils.extract_management_sentences(context, config.management_roles)
        if management_context.strip():
            context = management_context
            print("DEBUG: Extracted management context (first 300 chars):\n", context[:300])
    #if query about sponsors, extract relevant sentences    
    elif query_category_identified == 'sponsor':
        sponsor_context = text_utils.extract_sponsor_sentences(context)
        if sponsor_context.strip():
            context = sponsor_context
            print("DEBUG: Extracted sponsor context (first 300 chars):\n", context[:300])
    
    
    # Generate response using GPT
    # Pass the system message from config
    print(f"DEBUG: Context *before* calling get_gpt_response (first 500 chars):\n {context[:500]}") 
    response = llm_services.get_gpt_response(user_message, context, cache)
    print(f"🤖 GPT Response: {response}")
    return JsonResponse({"response": response}) 
