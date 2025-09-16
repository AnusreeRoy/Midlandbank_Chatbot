# ChromaDB based chatbot implementation
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
import time, re
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

@api_view(["GET", "POST"])
def chatbot_response(request):
    """Handle chatbot responses using ChromaDB and GPT."""
    #load user input
    user_message = request.data.get("message", "").strip()
    
    if not user_message:
        return JsonResponse({"response": "Please enter a question about Midland Bank."})
    
    # Step: Handle expected follow-up values (age, location, etc.)
    if not user_message:
        return JsonResponse({"response": "Please enter a question about Midland Bank."})
    
    # Step: Handle follow-up values first
    followup_response = text_utils.handle_conversation_state(user_message, request)
    if followup_response:
        return JsonResponse({"response": followup_response})

    conversation_state = request.session.get("conversation_state", {})

    # Only ask for location if NOT already awaiting location or location_received
    if conversation_state.get("type") not in ["awaiting_location", "location_received"]:
        query_category_identified, _ = identify_query_category(user_message)
        if query_category_identified == "location":
            request.session["conversation_state"] = {"type": "awaiting_location"}
            request.session.modified = True
            return JsonResponse({
                "response": "Share your area or city, and I’ll list the closest branches."
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
        
    # Query normalization and alias handling
    # Apply role aliases first for common phrase standardization
    for phrase, alias in config.role_aliases.items():
        user_message = user_message.replace(phrase, alias) # Apply to original message too if needed for later use
    
    # Apply product/general aliases for query normalization
    user_message = text_utils.normalize_query_with_aliases(user_message, PRODUCT_ALIASES)
            
    user_message_lower = user_message.lower()
    
    # Identify query category        
    query_category_identified, _ = identify_query_category(user_message)
    print(f"DEBUG: Identified Query Category: {query_category_identified}")
            
    #Handle common greetings
    if user_message_lower in config.greetings:
        return JsonResponse({"response": config.greetings[user_message_lower]})  
       
    # Detect topic and handle follow-ups
    current_topic = text_utils.extract_topic_from_message(user_message)
    if current_topic is None:
        current_topic = last_topic
        print(f"📌 Follow-up detected. Retaining previous topic: {current_topic}")
    else:
        # print(f"💡 New topic inferred: {current_topic}")
        if last_topic and last_topic.lower() != current_topic.lower():
            print(f"🔄 Topic switched from {last_topic} → {current_topic}. History cleared.")
            chat_history = chat_history[-2:] # Keep last 2 turns for context
            request.session["chat_history"] = chat_history
            request.session.modified = True
        else:
            print(f"💡 New topic inferred: {current_topic}")    
        
    if not current_topic:
        return JsonResponse({"response": "Could not determine the topic. Please clarify your question."})

    request.session["last_topic"] = current_topic   # Save topic
    request.session["chat_history"] = chat_history  # Ensure chat history is stored
    request.session.modified = True
    
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
        return JsonResponse({"response": response})

    
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
        return JsonResponse({"response": response})
    
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
    
        return JsonResponse({"response": response})
    
    #SME product listing handling
    if "sme" in user_message_lower and "product" in user_message_lower:
        product_list = product_listing_service.get_sme_product_names()
        
        if not product_list:
            return JsonResponse({"response": "No SME products found."})
        
        context = "\n".join(f"- {p}" for p in product_list)
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)
        text_utils.append_to_chat_history(request, user_message, response)
        return JsonResponse({"response": response})
    
     #NRB product listing handling
    if "nrb" in user_message_lower and "product" in user_message_lower:
        product_list = product_listing_service.get_nrb_product_names()
        
        if not product_list:
            return JsonResponse({"response": "No NRB products found."})
        
        context = "\n".join(f"- {p}" for p in product_list)
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)
        text_utils.append_to_chat_history(request, user_message, response)
        return JsonResponse({"response": response})

          
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
                return JsonResponse({"response": response})
            else:
                return JsonResponse({"response": f"No {cat} products found."})
            
                    
    #Fuzzy match product names in user query
    # Load all known products
    all_products = product_listing_service.get_all_product_names()
    
   # Try to fuzzy match multiple products
    matched_products = product_utils.extract_multiple_products(user_message, all_products)
    
    if len(matched_products) == 2:
        print(f"🧠 Multiple products detected: {matched_products}")
    
        contexts = []
        for prod in matched_products[:2]:  # Compare first two matched products
            print(f"📄 Getting context for: {prod}")
            context = retrieval_services.get_relevant_chroma_data(prod)
            print(f"📄 Raw context length: {len(context) if context else 0}")
            print(f"📄 Context preview: {context[:300] if context else 'No context found'}")
            if context.strip():
                contexts.append(f"📌 *{prod}*\n{context.strip()}")
    
        if contexts:
            MAX_CONTEXT_LENGTH = 4000  # Adjust based on token limits
            processed_contexts = []
            for c in contexts:
                if len(c) > MAX_CONTEXT_LENGTH:
                    processed_contexts.append(product_utils.summarize_context(c, llm_services, cache, history=chat_history))
                else:
                    processed_contexts.append(c)
            comparison_prompt = (
                "Compare the following two Midland Bank products side by side based on their features, eligibility, "
                "benefits, and any other distinguishing aspects. Present the comparison in clear bullet points or a table if possible."
            )
            combined_context = "\n\n".join(processed_contexts)
            final_context = f"{comparison_prompt}\n\n{combined_context}"
    
            messages = llm_services.build_message_list(user_message, final_context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
    
            text_utils.append_to_chat_history(request, user_message, response)
            return JsonResponse({"response": response})
    
    # Fallback to single product match
    matched_product = product_utils.match_product_name(user_message, all_products)
    
    if matched_product:
        print(f"🎯 Fuzzy matched '{user_message}' → '{matched_product}'")
        raw_context = retrieval_services.get_relevant_chroma_data(matched_product)
        context = text_utils.sanitize_context(raw_context)
    
        if context.strip():
            messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            text_utils.append_to_chat_history(request, user_message, response)
            return JsonResponse({"response": response})
        else:
            return JsonResponse({"response": f"Sorry, I couldn't find specific information on {matched_product}."})

    
    # Get relevant information from ChromaDB
    print(f"🔍 Processing query: {current_topic}")
    start_time = time.time()
    # Pass all necessary config data to the service function
    raw_context = retrieval_services.get_relevant_chroma_data(current_topic)
    print("DEBUG: Raw context type: ", raw_context[:300])
    context = text_utils.sanitize_context(raw_context)
    end_time = time.time()
    print(f"⏳ ChromaDB Query Time: {end_time - start_time:.2f} seconds")
    print("DEBUG: Context directly from get_relevant_chroma_data (first 500 chars):\n", context[:300])
    
    
    if not context.strip():
        return JsonResponse({"response": "Sorry, I couldn’t find anything relevant for that. Could you please rephrase?"})
    
    # If the query is about board members, extract relevant lines
    if query_category_identified== 'board':
        board_context = text_utils.extract_board_sentences(context)
        if board_context.strip():
            formatted_board_context = "\n".join([
            f"• {line.strip()}" for line in board_context.splitlines()
        ])
        print("DEBUG: Extracted board context (first 300 chars):\n", formatted_board_context[:300])
        messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
        response = llm_services.get_gpt_response(messages, cache)
        return JsonResponse({"response": response})
            
    # If the query is about management, extract only relevant lines
    elif query_category_identified == 'management':
        management_context = text_utils.extract_management_sentences(context, config.management_roles)
        if management_context.strip():
            print("DEBUG: Extracted management context (first 300 chars):\n", management_context[:300])
            messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            return JsonResponse({"response": response})
    #if query about sponsors, extract relevant sentences    
    elif query_category_identified == 'sponsor':
        sponsor_context = text_utils.extract_sponsor_sentences(context)
        if sponsor_context.strip():
            print("DEBUG: Extracted sponsor context (first 300 chars):\n", sponsor_context[:300])
            messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
            response = llm_services.get_gpt_response(messages, cache)
            return JsonResponse({"response": response})
    
    
    # Generate response using GPT
    print(f"DEBUG: Context *before* calling get_gpt_response (first 500 chars):\n {context[:500]}") 
    messages = llm_services.build_message_list(user_message, context, cache, history=chat_history)
    response = llm_services.get_gpt_response(messages, cache)
    # Save to session
    text_utils.append_to_chat_history(request, user_message, response)
    print("DEBUG session before append", chat_history)
    print(f"🤖 GPT Response: {response}")
    
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
            return JsonResponse({"response": fallback_response})
        
    return JsonResponse({"response": response}) 
