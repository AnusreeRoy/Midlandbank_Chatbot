# ChromaDB based chatbot implementation
from django.http import JsonResponse
from rest_framework.decorators import api_view
import time, re, logging
logger = logging.getLogger(__name__)
# Import from your new modules
from chatbot.data import config #
from chatbot.services import retrieval_services
from chatbot.services.retrieval_services import identify_query_category
from chatbot.services import llm_services
from chatbot.services import product_listing_service
from chatbot.utils import text_utils
from chatbot.utils import product_utils
from chatbot.services.retrieval_services import cache
from chatbot.data.config import PRODUCT_ALIASES
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import base64, io

def index(request):
    return render(request, "chatbot/chatbot.html")


@csrf_exempt
@api_view(["GET", "POST"])
def chatbot_response(request):
    """Handle chatbot responses using ChromaDB and GPT."""
    #load user input
    input_message = request.data.get("message", "").strip()
    user_message_sanitized = text_utils.sanitize_for_llm(input_message)
    user_message = re.sub(r'[^\w\s]', '', user_message_sanitized.lower()).strip()

    print(f"User message: {user_message}")
    
    # 🎤 Voice input
    audio_file = request.FILES.get("audio")
    is_voice_input = bool(audio_file)

    if audio_file:
        audio_bytes = io.BytesIO(audio_file.read())
        audio_bytes.name = audio_file.name
        try:
            audio_bytes = llm_services.normalize_audio_to_wav(audio_bytes)
            user_message = llm_services.speech_to_text(audio_bytes)
            user_message = text_utils.sanitize_for_llm(user_message)
            print("transcribed text", user_message)
        except Exception as e:
            logger.error(f"Speech-to-text conversion failed: {e}")
            user_message = "could not process audio"

    
    if not user_message:
        if is_voice_input:
            user_message = "Audio received but speech could not be recognized clearly."
        else:
            return JsonResponse({"response": "Please enter a question about Midland Bank."})

    
         
    # Step: Handle follow-up values first
    followup_response = text_utils.handle_conversation_state(user_message, request)
    if followup_response:
        return JsonResponse({"response": followup_response})
 
    conversation_state = request.session.get("conversation_state", {})
    query_category_identified, _ = identify_query_category(user_message)

    # Only ask for location if NOT already awaiting location or location_received
    if conversation_state.get("type") not in ["awaiting_location", "location_received"]:
        # query_category_identified, _ = identify_query_category(user_message)
        if query_category_identified == "location":
            request.session["conversation_state"] = {"type": "awaiting_location"}
            request.session.modified = True
            return JsonResponse({
                "response": "Share your area or city, and I’ll list the closest branches."
            })


    # Handle amount flow
    if conversation_state.get("type") not in ["awaiting_amount", "amount_received"]:
        query_category_identified, _ = identify_query_category(user_message)
        if query_category_identified == "amount":
            request.session["conversation_state"] = {"type": "awaiting_amount"}
            request.session.modified = True
            return JsonResponse({
                "response": "Please enter the loan amount you’d like me to check eligibility for."
            })

    # Initialize session chat history
    chat_history = request.session.get("chat_history", [])
    print("DEBUG session before append", chat_history)
    
    last_topic = request.session.get("last_topic", None)
    print("DEBUG: Last category from session:", last_topic)
    
    # Step: Get last bot message (for follow-up handling)
    last_bot_message = text_utils.get_last_bot_message(chat_history)
    
    # Step: Reframe "yes", "ok", etc. into a meaningful follow-up using topic & bot response
    reframed_message = text_utils.reframe_confirmation_reply(user_message, last_topic, last_bot_message)
    if reframed_message:
        print(f"🛠️ Reframed user message: '{user_message}' → '{reframed_message}'")
        user_message = reframed_message
               
    #Handle common greetings
    normalized = text_utils.normalize_message(user_message)
    user_message_lower = user_message.lower()
    if normalized in config.greetings:
        return JsonResponse({"response": config.greetings[normalized]})

    # Avoid fuzzy matching confirmation words like "yes"
    confirmation_words = {"yes", "yeah", "yep", "sure", "ok", "okay", "no", "nope"}
    if normalized not in confirmation_words and len(normalized) >3:  # Limit length for greetings
        matched_key = text_utils.fuzzy_greeting_match(normalized, config.greetings)
        if matched_key:
            return JsonResponse({"response": config.greetings[matched_key]})
        
    
    # Check if query is banking-related
    if not text_utils.is_relevant_query(user_message):
        return JsonResponse({
            "response": "I didn't quite catch that. Could you please rephrase your question related to Midland Bank?"
        })
        
        
    # Query normalization and alias handling
    # Apply role aliases first for common phrase standardization
    for phrase, alias in config.role_aliases.items():
        if phrase == "md": 
            user_message = re.sub(rf"\b{phrase}\b", alias, user_message, flags=re.IGNORECASE)
        else:
            user_message = user_message.replace(phrase, alias) 
    print(user_message)
    
    # Apply product/general aliases for query normalization
    user_message = text_utils.normalize_query_with_aliases(user_message, PRODUCT_ALIASES)
    print(f"🔄 Normalized user message: {user_message}")
                
    # Identify query category        
    query_category_identified, _ = identify_query_category(user_message)
    print(f"DEBUG: Identified Query Category: {query_category_identified}") 
       
    # Detect topic and handle follow-ups
    current_topic = text_utils.extract_topic_from_message(user_message)
    if current_topic is None:
        current_topic = last_topic
        print(f"📌 Follow-up detected. Retaining previous topic: {current_topic}")
    else:
        # print(f"💡 New topic inferred: {current_topic}")
        if last_topic and last_topic.lower() != current_topic.lower():
            print(f"🔄 Topic switched from {last_topic} → {current_topic}. History cleared.")
            # chat_history = chat_history[-2:] # Keep last 2 turns for context
            # request.session["chat_history"] = chat_history
            # request.session.modified = True
        else:
            print(f"💡 New topic inferred: {current_topic}")    
        
    if not current_topic:
        return JsonResponse({"response": "Could not determine the topic. Please clarify your question."})

    request.session["last_topic"] = current_topic   # Save topic
    request.session["chat_history"] = chat_history  # Ensure chat history is stored
    request.session.modified = True
    
    # === Structured product list handling ===
    user_message_lower = text_utils.normalize_query_for_matching(user_message)
    if any(q in user_message_lower for q in config.general_product_queries):
        grouped = product_listing_service.list_products_grouped_by_category()
        if not grouped:
            return JsonResponse({"response": "No products found in the knowledge base."})
        
        response_lines = []
        response_lines.append("Midland Bank offers the following products:")
        for cat, products in sorted(grouped.items()):
            response_lines.append(f"{cat} Products")
            response_lines.extend(f"- {p}" for p in products)
            response_lines.append("")  # spacing
        return JsonResponse({"response": "\n".join(response_lines)})
    
    
    # === Islamic Product Listing with Subcategories ===
    if "islamic" in user_message_lower and "product" in user_message_lower:
        grouped = product_listing_service.list_islamic_products_grouped()
        
        if not grouped:
            return JsonResponse({"response": "No Islamic products found."})
        
        response_lines = ["📦*Midland Bank Islamic Products:*"]
        for subcat, products in grouped.items():
            if products:
                response_lines.append(f"{subcat} Products")
                response_lines.extend(f"- {p}" for p in products)
                
        response_text = "\n".join(response_lines)
        messages = llm_services.build_message_list(user_message, response_text, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)
        text_utils.append_to_chat_history(request, user_message, response)
        result = {"response": response,
                  "transcript": user_message}
        if is_voice_input:
            try:
                audio_bytes = llm_services.text_to_speech(response)
                result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"Text-to-speech conversion failed: {e}")
        
        return JsonResponse(result)
    
    #islamic loan query handling 
    if "islamic" in user_message_lower and "loan" in user_message_lower:
        grouped = product_listing_service.list_islamic_products_grouped()
        loan_products = grouped.get("Islamic Loan", [])
        
        if not loan_products:
            return JsonResponse({"response": "No Islamic loan products found."})
        
        context = "\n".join(f"- {p}" for p in loan_products)
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)  
        text_utils.append_to_chat_history(request, user_message, response)
        result = {"response": response,
                  "transcript": user_message}
        if is_voice_input:
            try:
                audio_bytes = llm_services.text_to_speech(response)
                result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"Text-to-speech conversion failed: {e}")
        
        return JsonResponse(result)
    
    #islamic savings query handling 
    if "islamic" in user_message_lower and "savings" in user_message_lower:
        grouped = product_listing_service.list_islamic_products_grouped()
        savings_products = grouped.get("Islamic Savings", [])
        
        if not savings_products:
            return JsonResponse({"response": "No Islamic savings products found."})
        
        context = "\n".join(f"- {p}" for p in savings_products)
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)      
        text_utils.append_to_chat_history(request, user_message, response)
        result = {"response": response,
                  "transcript": user_message}
        if is_voice_input:
            try:
                audio_bytes = llm_services.text_to_speech(response)
                result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"Text-to-speech conversion failed: {e}")
        
        return JsonResponse(result)
    
    #SME product listing handling
    if "sme" in user_message_lower and "product" in user_message_lower:
        product_list = product_listing_service.get_sme_product_names()
        
        if not product_list:
            return JsonResponse({"response": "No SME products found."})
        
        context = "\n".join(f"- {p}" for p in product_list)
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)
        text_utils.append_to_chat_history(request, user_message, response)
        result = {"response": response,
                  "transcript": user_message}
        if is_voice_input:
            try:
                audio_bytes = llm_services.text_to_speech(response)
                result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"Text-to-speech conversion failed: {e}")

        return JsonResponse(result)
    
     #NRB product listing handling
    if "nrb" in user_message_lower and "product" in user_message_lower:
        product_list = product_listing_service.get_nrb_product_names()
        
        if not product_list:
            return JsonResponse({"response": "No NRB products found."})
        
        context = "\n".join(f"- {p}" for p in product_list)
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)
        text_utils.append_to_chat_history(request, user_message, response)
        result = {"response": response,
                  "transcript": user_message}
        if is_voice_input:
            try:
                audio_bytes = llm_services.text_to_speech(response)
                result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.error(f"Text-to-speech conversion failed: {e}")

        return JsonResponse(result)

          
    # Category-specific product listing
    for cat, triggers in config.category_map.items():
        if any(k in user_message_lower for k in triggers) and "product" in user_message_lower:
            products = product_listing_service.list_products_by_category(cat)
            if products:
                context = "\n".join(f"- {p}" for p in products)
                messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
                response = llm_services.get_gpt_response(messages, cache)
                text_utils.append_to_chat_history(request, user_message, response)
                print("DEBUG session before append", chat_history)
                result = {"response": response,
                          "transcript": user_message}
                # If voice input, convert the GPT response to speech and add it to the result
                if is_voice_input:
                    try:
                        audio_bytes = llm_services.text_to_speech(response)
                        result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
                    except Exception as e:
                        logger.error(f"Text-to-speech conversion failed: {e}")
                # Return the response as a JSON object
                return JsonResponse(result)
            else:
                return JsonResponse({"response": f"No {cat} products found."})
            
                    
    #Fuzzy match product names in user query
    # Load all known products
    all_products = product_listing_service.get_all_product_names()
    
    if "agent banking" in user_message_lower and "mdb" not in user_message_lower:
        matched_products = []
    else:
        # Try to fuzzy match multiple products
        matched_products = product_utils.extract_multiple_products(user_message, all_products)
    print(f"🔍 Fuzzy matched products: {matched_products}")
    
    if len(matched_products) == 2:
        print(f"🧠 Multiple products detected: {matched_products}")
    
        contexts = []
        for prod in matched_products[:2]:  # Compare first two matched products
            print(f"📄 Getting context for: {prod}")
            context = retrieval_services.get_relevant_chroma_data(prod)
            # print(f"📄 Raw context length: {len(context) if context else 0}")
            # print(f"📄 Context preview: {context[:300] if context else 'No context found'}")
            if context.strip():
                contexts.append(f"📌 *{prod}*\n{context.strip()}")
    
        if contexts:
            MAX_CONTEXT_LENGTH = 2500  # Adjust based on token limits
            summarization_start_time = time.time()
            processed_contexts = []
            for c in contexts:
                if len(c) > MAX_CONTEXT_LENGTH:
                    processed_contexts.append(product_utils.summarize_context(c, llm_services, cache, history=chat_history))
                    # print(f"🗜️ Summarized context length: {len(processed_contexts)}")
                else:
                    processed_contexts.append(c)
            summarization_end_time = time.time()
            print(f"⏱️ Context summarization took {summarization_end_time - summarization_start_time:.2f} seconds")        
            comparison_prompt = (
                "Compare the following two Midland Bank products side by side based on their features, eligibility, "
                "benefits, and any other distinguishing aspects. Present the comparison in clear bullet points or a table if possible."
            )
            combined_context = "\n\n".join(processed_contexts)
            final_context = f"{comparison_prompt}\n\n{combined_context}"
    
            messages = llm_services.build_message_list(user_message, final_context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            logger.info(f"🤖 GPT Comparison Response: {response}")
            text_utils.append_to_chat_history(request, user_message, response)
            result = {"response": response,
                      "transcript": user_message}
            if is_voice_input:
                try:
                    audio_bytes = llm_services.text_to_speech(response)
                    result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
                except Exception as e:
                    logger.error(f"Text-to-speech conversion failed: {e}")

            return JsonResponse(result)
    
    # Fallback to single product match
    # Prevent generic Agent Banking queries from being treated as a product
    branch_keywords = ["branch", "branches", "sub branch", "sub branches"]
    generic_agent_queries = ["agent banking", "agent services", "agent features", "agent eligibility", "agent documents","agent banking centre"]
    if any(gq in user_message_lower for gq in generic_agent_queries):
        matched_product = None
    elif any(bk in user_message_lower for bk in branch_keywords):   
        matched_product = None
    else:
        matched_product = product_utils.match_product_name(user_message, all_products)
    
    if matched_product:
        print(f"🎯 Fuzzy matched '{user_message}' → '{matched_product}'")
        raw_context = retrieval_services.get_relevant_chroma_data(matched_product)
        context = text_utils.sanitize_context(raw_context)
    
        if context.strip():
            messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            text_utils.append_to_chat_history(request, user_message, response)
            result = {"response": response,
                      "transcript": user_message}
            if is_voice_input:
                try:
                    audio_bytes = llm_services.text_to_speech(response)
                    result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
                except Exception as e:
                    logger.error(f"Text-to-speech conversion failed: {e}")

            return JsonResponse(result)
        else:
            return JsonResponse({"response": f"Sorry, I couldn't find specific information on {matched_product}."})

    
    # Get relevant information from ChromaDB
    print(f"🔍 Processing query: {current_topic}")
    start_time = time.time()
    # Pass all necessary config data to the service function
    raw_context = retrieval_services.get_relevant_chroma_data(current_topic)
    # print("DEBUG: Raw context type: ", raw_context[:300])
    context = text_utils.sanitize_context(raw_context)
    print(f"🔍 Retrieved context length: {len(context)}")
    
    end_time = time.time()
    print(f"⏳ ChromaDB Query Time: {end_time - start_time:.2f} seconds")
    # print("DEBUG: Context directly from get_relevant_chroma_data (first 500 chars):\n", context[:300])
    
    
    if not context.strip():
        return JsonResponse({"response": "Sorry, I couldn’t find anything relevant for that. Could you please rephrase?"})
    
    # # If the query is about board members, extract relevant lines
    # if query_category_identified== 'board':
    #     board_context = text_utils.extract_board_sentences(context)
    #     if board_context.strip():
    #         formatted_board_context = "\n".join([
    #         f"• {line.strip()}" for line in board_context.splitlines()
    #     ])
    #     # print("DEBUG: Extracted board context (first 300 chars):\n", formatted_board_context[:300])
    #     messages = llm_services.build_message_list(user_message, board_context, cache, history=chat_history)
    #     response = llm_services.get_gpt_response(messages, cache)
    #     result = {"response": response,
    #               "transcript": user_message}
    #     if is_voice_input:
    #         try:
    #             audio_bytes = llm_services.text_to_speech(response)
    #             result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
    #         except Exception as e:
    #             logger.error(f"Text-to-speech conversion failed: {e}")

    #     return JsonResponse(result)
            
    # If the query is about management, extract only relevant lines
    if query_category_identified == 'management':
        management_context = text_utils.extract_management_sentences(context, config.management_roles)
        if management_context.strip():
            print("DEBUG: Extracted management context (first 300 chars):\n", management_context[:300])
            print("management role",user_message)
            messages = llm_services.build_message_list(user_message, management_context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            result = {"response": response,
                      "transcript": user_message}
            if is_voice_input:
                try:
                    audio_bytes = llm_services.text_to_speech(response)
                    result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
                except Exception as e:
                    logger.error(f"Text-to-speech conversion failed: {e}")
            
            return JsonResponse(result)
    #if query about sponsors, extract relevant sentences    
    elif query_category_identified == 'sponsor':
        sponsor_context = text_utils.extract_sponsor_sentences(context)
        if sponsor_context.strip():
            # print("DEBUG: Extracted sponsor context (first 300 chars):\n", sponsor_context[:300])
            messages = llm_services.build_message_list(user_message, sponsor_context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            result = {"response": response,
                      "transcript": user_message}
            if is_voice_input:
                try:
                    audio_bytes = llm_services.text_to_speech(response)
                    result["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")
                except Exception as e:
                    logger.error(f"Text-to-speech conversion failed: {e}")

            return JsonResponse(result)
    
    
    # Generate response using GPT
    # print(f"DEBUG: Context *before* calling get_gpt_response (first 500 chars):\n {context[:500]}") 
    llm_start_time = time.time()
#     summarized_context = llm_services.prepare_context_for_llm(
#     raw_context=context,
#     cache=cache
# )
#     print(f"🔍 Summarized context length: {len(summarized_context)}")
    messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
    response = llm_services.get_gpt_response(messages, cache)
    llm_end_time = time.time()
    print(f"⏱️ LLM response generation took {llm_end_time - llm_start_time:.2f} seconds")
    # Save to session
    text_utils.append_to_chat_history(request, user_message, response)
    # print("DEBUG session before append", chat_history)
    print(f"🤖 GPT Response: {response}")
    # If the input was voice, convert the GPT response to speech and return audio
    if is_voice_input:
        audio_bytes = llm_services.text_to_speech(response)
        result = {
            "response": response,
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8")
        }
        return JsonResponse(result)
    # Fallback product listing if GPT doesn't help
    if (
        product_listing_service.is_product_list_request(user_message)
        and current_topic
        and (
            not response.strip()
            or "sorry" in response.lower()
            or "not sure" in response.lower()
            or "couldn’t find" in response.lower()
        )
    ):
        print(f"⚠️ GPT was uncertain. Attempting fallback product list for: {current_topic}")
        category_products = product_listing_service.list_products_by_category(current_topic)
    
        if category_products:
            bullet_list = "\n- " + "\n- ".join(category_products)
            fallback_response = f"I couldn’t find detailed info, but here are other {current_topic.title()} products:\n{bullet_list}"
            text_utils.append_to_chat_history(request, user_message, fallback_response)
            # If voice input, return the fallback response as speech too
            if is_voice_input:
                audio_bytes = llm_services.text_to_speech(fallback_response)
                result = {
                    "response": fallback_response,
                    "audio_base64": base64.b64encode(audio_bytes).decode("utf-8")
                }
                return JsonResponse(result)

            return JsonResponse({"response": fallback_response})
        
    return JsonResponse({"response": response}) 
