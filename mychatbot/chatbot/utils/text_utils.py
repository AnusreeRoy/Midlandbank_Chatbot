import re
from fuzzywuzzy import fuzz
from chatbot.data.config import bank_keywords

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

def truncate_context(context, max_chars=6000):
    if len(context) <= max_chars:
        return context
    truncated = context[:max_chars]
    last_period = truncated.rfind('.')
    if last_period == -1 or last_period < max_chars * 0.5:
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


def normalize_query_with_aliases(query: str, aliases: dict) -> str:
    query_lower = query.lower()
    sorted_aliases = sorted(aliases.items(), key=lambda x: len(x[0]), reverse=True)  # Prioritize longer phrases

    for alias_phrase, canonical_name in sorted_aliases:
        alias_phrase_lower = alias_phrase.lower()
        if alias_phrase_lower in query_lower:
            query = query.replace(alias_phrase, canonical_name)
            query_lower = query.lower()  # Update after each replacement
    return query

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
