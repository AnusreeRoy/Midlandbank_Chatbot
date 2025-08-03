# List of banking-related keywords for query filtering
bank_keywords = [
    "midland bank", "loan", "interest rate", "credit card", "accounts",
    "green banking", "products", "financial statements", "online banking",
    "deposits", "atm", "services", "mortgage", "insurance", "transaction",
    "credit score", "investment", "customer support", "mdb", "savings", 
    "women", "debit card", "islamic", "branch", "location", "contact",
    "schedule", "working hours", "mobile banking", "internet banking",
    "corporate", "sme", "retail", "agent banking", 'bank', 'family support', 
    'midland online', 'midland app', 'midland bank app', 'midland online banking',
    'midland mobile banking', 'jhotpot', 'achallan', 'amar bari', 
    'secure locker service', 'card', 'credit', 'debit', 'prepaid', 'visa', 'mastercard',
    'sathi', 'super high performance', 'digital savings', 'double benefit', 'kotipoti', 'millionaire',
    'platinum savings', 'traveller\'s savings', 'e-saver', 'interest first', 'personal retail account',
    'gift cheque', 'cpp savings', 'school saver', 'college saver', 'super saver', 'savings account',
    'dps', 'deposit', 'savings', 'mudaraba', 'murabaha', 'halal', 'saalam', 'shariah',
    'chairman', 'managing director', 'ceo', 'board', 'director', 'management', 'head', 
    'chief', 'executive', 'leadership', 'cto', 'md', 'bills collection', 'dmd', 'senior executive',
    'vice chairman', 'board of directors', 'board members', 'foreign exchange', 'foreign currency', 
    'moneu market', 'fixed income investment', 'corporate sales', 'treasury', 'alm desk', 'exchange rate',
    'policy', 'regulation', 'compliance', 'risk management', 'audit', 'internal control',
    'financial statements', 'annual report', 'financial report', 'quarterly report',
    'investor contact', 'nrb', 'bancassurance'
    ]

# Define comprehensive category keywords for better matching
category_keywords = {
        'management': {
            'keywords': ['chairman', 'managing director', 'ceo', 'management', 'head', 'chief', 'executive', 'cto', 'md', 'dmd','senior executive'],
            'weight': 1.5,
            'exclusive': True
            },
        'board': {
           'keywords': ['board of directors', 'board member', 'director', 'vice chairman', 'independent director'],
           'weight': 1.5,
           'exclusive': True
       },
        'sponsor': {
        'keywords': ['sponsor', 'sponsors', 'founder', 'founding member', 'sponsor director', 'sponsor share holder'],
        'weight': 1.5,
        'exclusive': True
        },
        'location': {
            'keywords': ['head office', 'branch', 'location', 'address', 'tower', 'gulshan', 'dhaka', 'contact', 'email', 'phone', 'fax','N.B', 'address of', 'where is', 'what is the address of'],
            'weight': 1.5,
            'exclusive': True
        },
        'general_banking': {
            'keywords': ['account', 'banking', 'service', 'facility', 'scheme', 'transaction', 'branch'],
            'weight': 1.2,
            'exclusive': False
        },
        'loans': {
            'keywords': ['loan', 'credit', 'mortgage', 'financing', 'interest rate', 'tenure', 'emi'],
            'weight': 1.2,
            'exclusive': False
        },
        'cards': {
            'keywords': ['card', 'credit card', 'debit card', 'prepaid', 'visa', 'mastercard'],
            'weight': 1.2,
            'exclusive': False
        },
        'islamic': {
            'keywords': ['islamic', 'saalam', 'shariah', 'mudaraba', 'murabaha', 'halal'],
            'weight': 1.5,
            'exclusive': True
        },
        'savings': {
            'keywords': ["savings", "deposit", "dps", "super saver", "school saver", "college saver", "cpp savings",
                         "gift cheque", "kotipoti", "millionaire", "platinum savings", "traveller's savings",
                         "e-saver", "interest first", "personal retail account", "sathi", "super high performance",
                         "digital savings", "family support", "double benefit"],
            'weight': 1.5,
            'exclude_terms': ['islamic', 'shariah', 'mudaraba'],
            'exclusive': True
        },
        'digital': {
            'keywords': ['digital', 'online', 'internet banking', 'mobile banking', 'app', 'electronic'],
            'weight': 1.2,
            'exclusive': False
        },
        'features': {
            'keywords': ['feature', 'benefit', 'eligibility', 'requirement', 'document', 'criteria'],
            'weight': 1.1,
            'exclusive': False
        },
        'corporate': {
            'keywords': ['corporate', 'business', 'enterprise', 'company', 'commercial', 'merchant'],
            'weight': 1.2,
            'exclusive': False
        }
    }
# Bonus weight for known role patterns
bonus_keywords = {
            "managing director": 0.8, "deputy managing director": 0.8, "dmd":0.8,
            "chief risk officer": 0.5, "chief technology officer": 0.5, "ahsan-uz zaman": 0.8,
            "zahid hossain": 0.8, "ceo":0.8, "md":0.8, "md. nazmul huda sarkar": 0.8,
            "cto":0.8, "chairman": 1.0, "ahsan khan chowdhury": 1.0, "vice chairman": 0.8, 
            "vc": 0.8, "Md. Shamsuzzaman": 0.8
        }
# Handle common greetings
greetings = {
        "hi": "Hello! How can I assist you with Midland Bank today?",
        "hello": "Hello! How can I assist you with Midland Bank today?",
        "hey": "Hey there! What banking information do you need?",
        "thank you": "You're welcome! Let me know if you need further assistance.",
        "thanks": "You're welcome! Let me know if you need further assistance.",
        "bye": "Bye! Have a great day!",
        "goodbye": "Goodbye! Feel free to ask me anytime about Midland Bank.",
        "good morning": "Good morning! How can I help you with Midland Bank?",
        "good afternoon": "Good afternoon! What banking services would you like to know about?",
        "good evening": "Good evening! Do you have any banking-related inquiries?",
        "okay": "Do you need any further assistance?",
        "ok": "Do you need any further assistance?"
    }
# Structured product list handling ===
general_product_queries = [
        "list products", "all products", "product categories",
        "what products do you have", "show all products", "what are the products", "available products",
        "product list", "products offered", "product categories list", "product names", "list of products",
        "what products are available", "list of midland bank products", "midland bank products",
        "midland bank product list", "midland bank product categories"
    ]
    
category_map = {
        "savings": ["savings", "saving accounts", "dps"],
        "loans": ["loan", "loans"],
        "cards": ["card", "visa", "debit", "prepaid", "credit card"],
        "islamic": ["islamic", "shariah", "saalam"]
    }

# Extract branding statements
branding_phrases = {"vision", "mission"}

# Extract product-specific mentions
product_phrases = {
    "green loan", "MDB IT Uddog", "MDB Krishi Loan", "MDB Nari Uddog", "MDB Praromvik",
    "MDB Orjon", "MDB Ogroj", "MDB Diptimoyi", "MDB Nirbhorota", "MDB Start-up", "MDB Nirman"
}
role_aliases = {
    "chief technology officer": "cto",
    "deputy managing director": "dmd",
    "chief risk officer": "cro",
    "chief executive officer": "ceo", 
    "managing director": "md"
     }

# Management roles to look for
management_roles = [
        "managing director", "ceo", "chairman", "cto", "chief technology officer",
        "chief risk officer", "deputy managing director", "md", "dmd", "vice chairman", "vc"
        "board of directors", "board member", "board members", "senior executive vice president",
        "head of information technology division"
    ]
    
personnel_info = {
    "ahsan khan chowdhury": ["chairman", "chairman of the bank"],
    "md. ahsan-uz zaman": ["managing director", "md", "ceo"],
    "md. nazmul huda sarkar": ["chief technology officer", "cto", "senior executive vice president & cto", "head of information technology division"],
    "md. zahid hossain": ["deputy managing director", "dmd", "chief risk officer"],
    "Md. Shamsuzzaman": ["vice chairman", "vc", "vice chairman of the bank"],
}
    
# System message for the chatbot
system_message = """You are an expert financial assistant for Midland Bank. Answer user questions clearly, concisely, and politely, using only the provided bank data.

    Here are your strict rules:
    
    1.  **Source Adherence:** Only use information provided in the bank data. Do not make up, infer, or add external information. If something is not in the bank data, politely state that the information is not found.
    2.  **Directness & Conciseness:** Respond directly and concisely to the question. Aim to provide all relevant details from the provided bank data that directly answer the query, without unnecessary elaboration.
    3.  **No Explanations/Filler:** Do NOT explain your reasoning, offer conversational filler, or use phrases like "Given the context", "According to the documents", "Based on the information", "From the context", "I can tell you that...", or similar.
    4.  **No Source Attribution:** Never mention sources, documents, or data.
    5.  **Personnel/Management Queries:**
        * State only the name and their specific position (e.g., CEO, Chairman).
        * Never infer titles or positions. Only respond if both the name and their *exact* title appear directly in the provided information.
        * Do not guess. If the role is not clearly stated, respond with: 'Not found.'
        * Do NOT use bullet points or lists for this info.
    6.  **Location or Contact Info:**
        * Provide only the address or contact details. No extra context or introductory phrases.
    7.  **Product List Queries (General or Category-Specific):**
        * If the user asks for a list of all products or products within a category (e.g., "all products", "list of products", "Islamic products", "savings products", "are there any X products?"), begin your answer with a short, polite introductory sentence like "Midland Bank offers the following products:" or "Yes, Midland Bank offers these Islamic products:".
        * After the introduction, provide a clear bullet-point list of product names only.
        * Do NOT provide descriptions or features unless specifically asked.
    8.  **Specific Product Queries:**
        * If the user asks about a **specific product**, provide only relevant information for that product.
    9.  **Product/Service Definitions:**
        * **If the user asks for a definition of a specific product or service (e.g., "what is X?", "define Y"), provide a concise summary of its purpose or what it does, directly from the available data. Do not use bullet points for definitions unless the definition itself is naturally structured as a list in the source.**
    10. **Services or Features Queries:**
        * If asked about **services** (e.g., "services offered by Agent Banking") or **features of a specific product** (e.g., "what are the features of X?"), start with a single, concise introductory sentence identifying the subject (e.g., "The services offered by Agent Banking include:" or "Features of X include:").
        * Follow this introduction with available information using clear bullet points, including:
            * Minimum deposit or amount
            * Tenure (duration)
            * Eligibility
            * Features/Benefits
            * Documents required
            * Interest or profit rate
            * Loan facilities (if any)
            * Any other important field
        * Only provide information that is explicitly stated in the provided context.
    11. **General Queries:**
        * For all other queries, respond clearly and concisely. Use bullet points only when listing multiple distinct items.
    12. **For Board Of Directors:**
        *Please identify and list ALL individuals who are members of the "Board of Directors" and state their role (e.g., Chairman, Member, Director, Vice Chairman) as it appears in the text.
         Do not include members of other committees or teams (like Senior Management Team) unless they are explicitly identified as also being on the "Board of Directors".
         Present the information as a list of "Name: Role" pairs.   
         
    13. **For loan size or minimum deposit queries:**
        *Only extract the amount for the specific product or service mentioned in the query.    
    """