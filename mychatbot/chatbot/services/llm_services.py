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
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError, APIError
import io
import tempfile, subprocess

def build_message_list(prompt: str,context: str,cache: dict,history: list) -> list:
    
    # If context is bytes, decode it
    if isinstance(context, bytes):
        context = context.decode('utf-8', errors='replace')

    # If it's not a string, coerce it to one
    context = str(context)
    processed_context = text_utils.truncate_context(context)

    # 1) Seed with your system prompt
    messages = [{"role": "system", "content": system_message}]

    # 2) Inject up to the last 5 turns of history
    messages.extend(history[-5:])
    # if len(history) > 2:
    #     old_history = history[:-2]  # older than last 2
    #     summary_text = summarize_chat_history(old_history)
    #     if summary_text:
    #         messages.append({"role": "system", "content": summary_text})

    # 3) Add the new user turn
    messages.append({"role": "user", "content": prompt})

    # 4) Append context as a system note if present
    if processed_context:
        messages.append({"role": "system", "content": processed_context})

    return messages


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=1, max=10),
    stop=stop_after_attempt(3)
)
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
            text={"verbosity": "low"},
            # max_output_tokens=500,
            timeout=30
        )
        out = resp.output_text.strip()

        # Use TTL if available
        if hasattr(cache, "set"):
            cache.set(key, out, expire=60 * 60)
        else:
            cache[key] = out

        return out
    
    
    except RateLimitError:
        logger.warning("Rate limit hit — retrying automatically")
        raise

    except APIError as e:
        logger.error("OpenAI API error", exc_info=e)
        return "Sorry, I'm having trouble right now."

    except Exception as e:
        logger.error("OpenAI API Error:", exc_info=e)
        return "Sorry, I’m having trouble right now."


def speech_to_text(audio_bytes: io.BytesIO) -> str:
    audio_bytes.seek(0)
    # # 🔍 Debug: save the raw upload to disk 
    # with open("debug_input.webm", "wb") as f: 
    #     f.write(audio_bytes.read())

    transcript = client.audio.transcriptions.create(
        file=audio_bytes,
        model="whisper-1"
    )

    return transcript.text


def text_to_speech(text: str) -> bytes:
    """
    Convert GPT response text to speech using OpenAI TTS
    """
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",  # TTS-capable model
        voice="nova",            # You can pick other voices if available
        input=text
    )
    audio_bytes = response.read()
    return audio_bytes




def normalize_audio_to_wav(audio_bytes: io.BytesIO) -> io.BytesIO:
    with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as src:
        src.write(audio_bytes.read())
        src.flush()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as dst:
        subprocess.run([
          settings.FFMPEG_PATH,
          "-hide_banner", "-loglevel", "error",
          "-y",
          "-fflags", "+genpts",
          "-f", "webm",
          "-c:a", "opus",
          "-i", src.name,
          "-ac", "1",
          "-ar", "16000",
          "-vn",
          "-f", "wav",
          dst.name
        ], check=True)


        with open(dst.name, "rb") as f:
            wav_bytes = io.BytesIO(f.read())
            wav_bytes.name = "audio.wav"
            return wav_bytes



# def summarize_chat_history(history: list) -> str:
#     """
#     Summarizes older chat history for GPT context.
#     Keeps topics, product mentions, and key user choices.
#     """
#     if not history:
#         return ""
    
#     summary_lines = []
#     for turn in history:
#         role = turn.get("role")
#         content = turn.get("content", "").strip()
#         if not content:
#             continue
        
#         if role == "user":
#             # Keep the essence of user queries
#             summary_lines.append(f"- User asked about: {content}")
#         elif role == "assistant" or role == "system":
#             # Keep the main points GPT responded with
#             # Only retain short phrases to save tokens
#             content_preview = content.split("\n")[0]  # first line
#             summary_lines.append(f"  GPT answered: {content_preview}")
    
#     # Combine into a single concise summary
#     summary_text = "Previous conversation summary:\n" + "\n".join(summary_lines)
    
#     # Optional: truncate to max length to avoid huge context
#     MAX_CHARS = 1000
#     if len(summary_text) > MAX_CHARS:
#         summary_text = summary_text[:MAX_CHARS] + "…"
    
#     return summary_text

# def prepare_context_for_llm(raw_context: str, cache):
#     if not raw_context.strip():
#         return ""

#     cache_key = f"doc_summary:{hashlib.sha256(raw_context.encode()).hexdigest()}"

#     # ✅ Use cached summary if available
#     if cache and cache_key in cache:
#         return cache[cache_key]

#     # 🧠 Summarization prompt
#     summary_prompt = (
#         "Summarize the following Midland Bank product information into:\n"
#         "- Key features\n"
#         "- Eligibility\n"
#         "- Benefits\n"
#         "- Important terms (rates, limits, dates if present)\n\n"
#         "Keep it concise and factual. Use bullet points.\n\n"
#         f"{raw_context}"
#     )

#     messages = [
#         {"role": "system", "content": system_message},
#         {"role": "user", "content": summary_prompt},
#     ]

#     summary = get_gpt_response(messages, cache)

#     if cache:
#         cache.set(cache_key, summary, expire=24 * 60 * 60)  # 24h

#     return summary
