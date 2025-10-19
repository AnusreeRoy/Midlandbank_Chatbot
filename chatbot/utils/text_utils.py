import re
from fuzzywuzzy import fuzz
from difflib import get_close_matches
from chatbot.data.config import bank_keywords
from chatbot.services import llm_services
from chatbot.services.retrieval_services import cache
from chatbot.services import retrieval_services

def normalize_message(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Expand common abbreviations
    replacements = {
        "u": "you",
        "r": "are",
        "ur": "your",
        "pls": "please",
        "thx": "thanks"
    }
    words = text.split()
    expanded = [replacements.get(w, w) for w in words]
    return ' '.join(expanded)


def fuzzy_greeting_match(text, greetings_dict):
    normalized = normalize_message(text)
    matches = get_close_matches(normalized, greetings_dict.keys(), n=1, cutoff=0.6)
    return matches[0] if matches else None



def is_relevant_query(user_message):
    """Check if query is banking-related using fuzzy matching."""
    for keyword in bank_keywords:
        if fuzz.partial_ratio(user_message.lower(), keyword) > 60:
            return True
    return False

def clean_response(text):
    """Remove forbidden starting phrases and sentences mentioning 'context'."""
    forbidden_starts = [
        r"(?i)^(based on|according to|as per|given the|from the information|it appears|looking at|the context).*"
    ]
    lines = text.split('\n')
    clean_lines = [line for line in lines if not any(re.match(p, line.strip()) for p in forbidden_starts)]
    # Remove sentences containing the word 'context'
    clean_text = []
    for line in clean_lines:
        sentences = line.split('.')
        filtered_sents = [s for s in sentences if "context" not in s.lower()]
        clean_text.append('.'.join(filtered_sents).strip())
    return "\n".join(clean_text).strip()

def truncate_context(context, max_chars=4000, fallback_min=1000):
    if len(context) <= max_chars:
        return context
    truncated = context[:max_chars]
    last_period = truncated.rfind('.')
    if last_period == -1 or last_period < fallback_min:
        return truncated.strip() + " ..."
    return truncated[:last_period+1]

def deduplicate_lines(text):
    seen = set()
    deduped = []
    for line in text.splitlines():
        line = line.strip()
        if line and line not in seen:
            deduped.append(line)
            seen.add(line)
    return "\n".join(deduped)

def normalize_block_spacing(text):
    # Add newlines between capitalized names for more accurate splitting
    return re.sub(r'(?<=\w)(?=Mr\.|Mrs\.|Dr\.|Md\.|Master|Ms\.|Ahsan)', '\n', text)


def extract_management_sentences(context, role_keywords):
    """Extract sentences mentioning management roles from the context."""
    sentences = re.split(r'(?<=[.?!])\s+', context.strip())
    relevant = []
    for sentence in sentences:
        if any(re.search(rf'\b{re.escape(role)}\b', sentence, re.IGNORECASE) for role in role_keywords):
            relevant.append(sentence.strip())
    return "\n".join(relevant)

def extract_board_sentences(context, board_keywords=None):
    if board_keywords is None:
        board_keywords = [
            "board of directors", "director", "chairman", "vice chairman",
            "independent director", "board member", "sponsor director"
        ]

    # Normalize spacing before splitting
    context = normalize_block_spacing(context)
    context = deduplicate_lines(context)

    # Use smart line splitting fallback
    lines = re.split(r'(?<=[.?!])\s+|\n+', context.strip())
    relevant = []
    seen = set()

    for line in lines:
        line_clean = line.strip()
        if any(re.search(rf'\b{re.escape(role)}\b', line_clean, re.IGNORECASE) for role in board_keywords):
            if line_clean not in seen:
                seen.add(line_clean)
                relevant.append(line_clean)

    return "\n".join(relevant)


def extract_sponsor_sentences(context: str, sponsor_keywords=None):
    """Extract sentences or blocks mentioning sponsors or founders."""
    if sponsor_keywords is None:
        sponsor_keywords = [
            "sponsor of midland bank", "sponsor", "sponsors", 
            "sponsor director", "founder", "founding member", 
            "sponsor shareholders"
        ]
        
    # Lowercase context for matching, but retain original for output
    context_lower = context.lower()
    blocks = re.split(r'[\n\r]+', context.strip())
    relevant = []
    seen = set()

    for block in blocks:
        block_lower = block.lower()
        if any(k in block_lower for k in sponsor_keywords):
            # Clean and dedupe block
            block_clean = block.strip()
            if block_clean and block_clean not in seen:
                seen.add(block_clean)
                relevant.append(block_clean)

    # Fallback: if no block matched but sponsor chunk confirmed, return whole
    if not relevant and any(k in context_lower for k in sponsor_keywords):
        return context.strip()

    return "\n".join(relevant)


import re

def normalize_query_for_matching(query: str) -> str:
    query = query.lower().strip()
    query = re.sub(r'\bu\b', 'you', query)         # Replace u → you
    query = re.sub(r'[^\w\s]', '', query)          # Remove punctuation like ? or !
    return query


def normalize_query_with_aliases(query: str, aliases: dict) -> str:
    # Sort by descending alias length to match longer phrases first
    sorted_aliases = sorted(aliases.items(), key=lambda x: -len(x[0]))

    # Keep track of replaced spans to avoid double replacements
    replaced_spans = []

    def replacement_func_factory(start, end, canonical_name):
        def replace_func(match):
            # Ensure the match doesn't overlap any existing replacements
            match_span = match.span()
            for span in replaced_spans:
                if not (match_span[1] <= span[0] or match_span[0] >= span[1]):
                    return match.group()  # Overlaps, skip replacement
            replaced_spans.append(match_span)
            return canonical_name
        return replace_func

    # Work on a copy so we can track replacements properly
    result = query

    for alias, canonical in sorted_aliases:
        pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(result):
            replacement_func = replacement_func_factory(*match.span(), canonical)
            result = pattern.sub(replacement_func, result, count=1)  # Replace one at a time to preserve spans

    return result


def extract_target_phrases(context, target_phrases):
    """
    Extract sentences from context that mention any of the target phrases.
    Useful for isolating product names or branding statements from compound chunks.
    """
    sentences = re.split(r'(?<=[.?!])\s+', context.strip())
    relevant = []
    for sentence in sentences:
        if any(re.search(rf'\b{re.escape(phrase)}\b', sentence, re.IGNORECASE) for phrase in target_phrases):
            relevant.append(sentence.strip())
    return "\n".join(relevant)


# === Topic Detection ===
def extract_topic_from_message(message: str):
    """
    Extracts topic/product name from user message. 
    If message is vague or purely follow-up, returns None.
    """
    follow_up_keywords = [
        "its features", "eligibility", "requirements", "needed",
        "documents", "interest rate", "where to get", "benefits",
        "how to apply", "how does it work", "what are the benefits",
        "can i apply", "tell me more", "explain its features", "next steps",
        "what's the process", "application process", "open it", "what about it",
        "next steps", "what's next", "i want to know more", "i want to apply",
        "guide me", "more info", "details please"
    ]
    message_lower = message.lower().strip()
    
    # === New addition: Ignore short numeric or currency answers ===
    if re.fullmatch(r'(bdt|taka)?\s?[\d,.]+( years?)?', message_lower) or re.fullmatch(r'[\d,.]+\s?(years?)?', message_lower):
        return None
    
    # Also ignore short replies that are likely parameters
    if len(message_lower.split()) <= 2 and any(char.isdigit() for char in message_lower):
        return None

    # If the message is very short and vague
    if len(message_lower.split()) < 3 and any(k in message_lower for k in follow_up_keywords):
        return None

    # Try extracting topic from question pattern
    match = re.search(r"(what is|tell me about|explain|define)\s+(.*?)($|\s(and|with)\s)", message_lower)
    if match:
        return match.group(2).strip()
    
    # Try fallback noun extraction if message includes 'and'
    parts = re.split(r'\s+and\s+|\s*,\s*', message_lower)
    for part in parts:
        if any(word in part for word in ['account', 'saver', 'loan', 'card', 'deposit']):
            return part.strip()

    return message_lower  # fallback


def sanitize_context(raw) -> str:
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    return str(raw)



def reframe_confirmation_reply(user_message, last_topic, last_bot_message):
    """
    Reframes vague replies like 'yes', 'how do I apply for it' etc.
    Replaces vague pronouns like 'it', 'this', 'that' with last_topic.
    Returns None if no reframing is needed.
    """

    confirmations = {
        "yes", "ok", "okay", "sure", "go ahead", "please do", "proceed", "alright",
        "tell me more", "elaborate", "how can i apply for it", "how do i apply", "apply for it",
        "more info", "details please", "what's the process", "what about it", "this", "that", "it",
        "guide me", "next steps", "what's next", "i want to know more", "i want to apply",
        "more details", "more information", "please continue", "continue", "go on"
    }
    rejections = {"no", "not now", "maybe later", "cancel", "never mind"}

    user_msg = user_message.strip().lower()

    if user_msg in rejections:
        return "No follow-up needed. Thank you!"

    if not last_topic:
        return None  # Can't fix vague refs if we don't know the topic

    # If user's message contains vague words like "it", "this", etc — replace them with topic
    if any(vague in user_msg for vague in {"it", "this", "that"}):
        rewritten = re.sub(r'\b(it|this|that)\b', last_topic, user_msg)
        return rewritten.strip()

    # If user message is one of the confirmations — reframe into generic follow-up
    if user_msg in confirmations:
        print("🧠 Using GPT to rephrase vague confirmation based on last bot question...")
        
        
        # Basic message structure
        gpt_messages = [ {"role": "system", "content": (
        "You are a bank assistant. Your task is to rephrase vague replies "
        "like 'yes', 'how do I apply for it', or 'tell me more' into clear, complete follow-up requests. "
        "Make sure the output is specific to the last topic. Be clear and concise."
        )},
        {"role": "user", "content": (
            f"The user said: '{user_msg}'. The previous bot message was: '{last_bot_message}'. "
            f"The topic is: '{last_topic}'.\n\nPlease convert the user reply into a clear follow-up request."
        )}]

        followup_rephrased = llm_services.get_gpt_response(gpt_messages, cache=cache)
        print(f"🔄 GPT rephrased: {followup_rephrased}")
        if not followup_rephrased or not followup_rephrased.strip():
            return f"Please continue explaining about {last_topic}."
    
        return followup_rephrased.strip()

    # Otherwise no reframing needed
    return None

def append_to_chat_history(request, user_message, bot_response):
    chat_history = request.session.get("chat_history", [])
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": bot_response})
    request.session["chat_history"] = chat_history[-10:]  # Keep last 10
    request.session.modified = True


def get_last_bot_message(chat_history):
    for msg in reversed(chat_history):
        if msg["role"] == "assistant":
            return msg["content"]
    return None


def handle_conversation_state(user_message, request):
    conversation_state = request.session.get("conversation_state", {})
    user_info = request.session.get("user_info", {})

    state_type = conversation_state.get("type")

    if state_type == "awaiting_location":
        location = user_message.strip().lower()
        user_info["location"] = location
        request.session["user_info"] = user_info

        # Instead of clearing, set to 'location_received' to mark we got location
        request.session["conversation_state"] = {"type": "location_received"}
        request.session.modified = True

        # Fetch branches from ChromaDB or fallback
        context = retrieval_services.get_relevant_chroma_data(location)
        sanitized = sanitize_context(context)

        if not sanitized.strip():
            return f"Thanks! Noted your location as **{location.title()}**, but I couldn't find any nearby branches."

        messages = llm_services.build_message_list(
            f"List Midland Bank branches near {location} with address, hours, email, and services.", 
            sanitized, 
            cache=None, 
            history=[]
        )
        response = llm_services.get_gpt_response(messages, cache=None)
        return response

    # Add other conversation states as needed

    return None
