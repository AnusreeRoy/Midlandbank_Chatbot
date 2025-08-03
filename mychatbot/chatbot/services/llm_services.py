from openai import OpenAI
from django.conf import settings 
import diskcache as dc
cache = dc.Cache("cache_dir")
from chatbot.utils.text_utils import clean_response
from chatbot.data.config import system_message
from chatbot.utils import text_utils
client = OpenAI(api_key=settings.API_KEY)

def get_gpt_response(user_message: str, context: str, cache: dict) -> str:
    
    processed_context = context or ""
    print("gpt context", context[:300])
    #processed_context = text_utils.deduplicate_lines(processed_context)
    processed_context = text_utils.truncate_context(processed_context)
    print("Processed context:", processed_context[:300])
    cache_key = f"gpt:{hash(user_message + processed_context)}"
    if cache_key in cache:
        print("⚡ GPT response from cache")
        return cache[cache_key]
    
    try:
        messages =[
            {"role": "system", "content": system_message}, 
        ]
        if context:
            messages.append({"role": "assistant", "content": processed_context})

        # Then user question:
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        
        gpt_response = response.choices[0].message.content
        cleaned_response = clean_response(gpt_response)
        
        # Store in cache if needed
        cache[cache_key] = cleaned_response
        
        return cleaned_response 
        
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return "I apologize, but I'm having trouble processing your request at the moment. Please try again."
