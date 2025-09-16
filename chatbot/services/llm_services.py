from openai import OpenAI
from django.conf import settings 
from chatbot.services.retrieval_services import cache
# from chatbot.utils.text_utils import clean_response
from chatbot.data.config import system_message
from chatbot.utils import text_utils
client = OpenAI(api_key=settings.API_KEY)

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
    messages.extend(history[-20:])

    # 3) Add the new user turn
    messages.append({"role": "user", "content": prompt})

    # 4) Append context as a system note if present
    if processed_context:
        messages.append({"role": "system", "content": processed_context})

    return messages


def get_gpt_response(messages: list, cache: dict) -> str:
    """
    Sends `messages` to GPT-5, caching by the hash of their content.
    """
    if cache is None:
        cache = {}
    key = f"gpt5:{hash(tuple((m['role'], m['content']) for m in messages))}"
    if key in cache:
        return cache[key]

    try:
        resp = client.responses.create(
            model="gpt-5",
            input=messages,
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"}
        )
        out = resp.output_text.strip()
        cache[key] = out
        return out
    except Exception as e:
        print("OpenAI API Error:", e)
        return "Sorry, I’m having trouble right now."