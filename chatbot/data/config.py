import os
import json
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
    'investor contact', 'nrb', 'bancassurance', 'sponsors', 'eligibility', 'requirements',
    'documents', 'criteria', 'features', 'benefits', 'minimum deposit', 'amount', 'tenure',
    'students', 'university','e-gp', 'corporate banking', 'business banking', 'merchant services', 'Excise duty',
    'RTGS'
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
            'keywords': ['islamic', 'saalam', 'shariah', 'mudaraba', 'murabaha', 'halal', 'islami'],
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
        "ok": "Do you need any further assistance?",
        "how are you": "I'm here and ready to help with any Midland Bank questions you have."
    }
# Structured product list handling ===
general_product_queries = [
        "list products", "all products", "product categories",
        "what products do you have", "show all products", "what are the products", "available products",
        "product list", "products offered", "product categories list", "product names", "list of products",
        "what products are available", "list of midland bank products", "midland bank products",
        "midland bank product list", "midland bank product categories", "what do you offer", 
        "what do you provide", "what are your services", "services you offer", "what are your offerings", 
        "show me what you offer", "show me your services", "services list", "your products", "your services", 
        "list your products", "tell me about your products", "do you have any products",
        "offerings", "bank offerings"
    ]
    
category_map = {
        "savings": ["savings", "saving accounts", "dps", "deposit", "deposit accounts","deposit products"],
        "loans": ["loan", "loans"],
        "cards": ["card", "visa", "debit", "prepaid", "credit card"],
        "Islamic Loan": ["islamic loan", "shariah-compliant loan", "halal loan", "saalam loan"],
        "Islamic Savings": ["islamic savings", "shariah savings", "halal savings", "mudaraba", "saalam savings"],
        "Islamic Current": ["islamic current", "shariah current account", "halal current", "saalam current"],
        "islamic": ["islamic", "shariah", "saalam"],  
        "women banking":["sathi", "Nari Uddog", "saalam sathi", ]
        
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
    "managing director": "md",
    "vice chairman": "vc",
     }

location_aliases = {
        'dhaka': ['dhaka', 'gulshan', 'fatullah', 'uttara', 'gazipur', 'banani', 'dhanmondi'],
        'chittagong': ['chittagong', 'agrabad', 'sompara'],
        'sylhet': ['sylhet'],
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
    
system_message = """
You're the Midland Bank AI Advisor — here to help customers with friendly, clear, and helpful answers.

Speak like a trusted banking partner: approachable, concise, and supportive.

Stick only to information provided by Midland Bank. If something isn’t in the data, be honest about it — don’t guess or make things up.

Here’s how to respond:
1. Use only what's in the bank’s data. If something’s not covered, say it simply — e.g., "I don't have details on that right now." Only say this if you truly can't help.
2. Don’t assume or infer details — stick to what’s clearly stated.
3. Keep it natural — skip phrases like "According to the document" or "Based on the context."
4. Use bullet points for listing features, benefits, or steps — it makes things easier to read.
5. Only mention roles like CEO or Chairman if they’re clearly included in the data.
6. Invite follow-up questions — make the user feel welcome to ask more.
7. If the user follows up with 'yes' or 'ok', assume they're referring to the last discussed topic.
"""


# Load product aliases from JSON
alias_path = os.path.join(os.path.dirname(__file__), "product_aliases.json")

try:
    with open(alias_path, "r", encoding="utf-8") as f:
        PRODUCT_ALIASES = json.load(f)
except FileNotFoundError:
    print("WARNING: product_aliases.json not found. Alias normalization might be limited.")
    PRODUCT_ALIASES = {}