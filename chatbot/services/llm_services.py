from openai import OpenAI
from django.conf import settings 
from chatbot.services.retrieval_services import cache
# from chatbot.utils.text_utils import clean_response
from chatbot.data.config import system_message
from chatbot.utils import text_utils
import hashlib
import json
client = OpenAI(api_key=settings.API_KEY)
import logging
logger = logging.getLogger(__name__)

def build_message_list(prompt: str,context: str,cache: dict,history: list) -> list:
    
    # If context is bytes, decode it
    if isinstance(context, bytes):
        context = context.decode('utf-8', errors='replace')

    # If it's not a string, coerce it to one
    context = str(context)
    processed_context = text_utils.truncate_context(context)

    # 1) Seed with your system prompt
    messages = [{"role": "system", "content": system_message}]

    # 2) Inject up to the last 20 turns of history
    messages.extend(history[-6:])

    # 3) Add the new user turn
    messages.append({"role": "user", "content": prompt})

    # 4) Append context as a system note if present
    if processed_context:
        messages.append({"role": "system", "content": processed_context})

    return messages



def get_gpt_response(messages: list, cache) -> str:
    """
    Sends `messages` to GPT-5, caching by the hash of their content.
    Supports TTL if cache is DiskCache.
    """
    if cache is None:
        logger.warning("No cache provided; using temporary in-memory cache")
        cache = {}

    model = getattr(settings, "DEFAULT_GPT_MODEL", "gpt-5")
    key_data = json.dumps(messages, sort_keys=True)
    key = f"{model}:{hashlib.sha256(key_data.encode()).hexdigest()}"

    if key in cache:
        return cache[key]

    try:
        resp = client.responses.create(
            model=model,
            input=messages,
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"}
        )
        out = resp.output_text.strip()

        # Use TTL if available
        if hasattr(cache, "set"):
            cache.set(key, out, expire=60 * 60)
        else:
            cache[key] = out

        return out

    except Exception as e:
        logger.error("OpenAI API Error:", exc_info=e)
        return "Sorry, I’m having trouble right now."
