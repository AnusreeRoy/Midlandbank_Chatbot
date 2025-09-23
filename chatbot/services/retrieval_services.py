from chatbot.data.config import category_keywords, bonus_keywords, personnel_info
import re
import chromadb
from tenacity import retry, wait_random_exponential, stop_after_attempt
from rest_framework.decorators import api_view
import os
from tenacity import retry, wait_random_exponential, stop_after_attempt
import chromadb
from chromadb.config import Settings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress INFO and WARNING logs
import diskcache as dc
cache = dc.Cache("cache_dir")  # Initialize disk cache for caching results
from chromadb.utils import embedding_functions
# Import the loaded product aliases data
from chatbot.apps import product_aliases_data as product_aliases
from chatbot.data import config 
from chatbot.utils.text_utils import normalize_query_with_aliases
import time

embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-base-en-v1.5"
)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=r"C:\Users\mdbl.plc\Scraper\chroma_rich",
    settings=Settings(
        anonymized_telemetry=False  # Disable telemetry for faster performance
    )
)

collection = chroma_client.get_collection(
    name="midland_detailed",
    embedding_function=embedding_func
)


def identify_query_category(query):
    """Identify the primary category of the query."""
    query_lower = query.lower()
    category_scores = {}
    for category, info in category_keywords.items():
        score = 0
        for keyword in info['keywords']:
            if re.search(rf'\b{re.escape(keyword.lower())}\b', query_lower):
                score += 1
        if score > 0:
            category_scores[category] = score * info['weight']
    if not category_scores:
        return None, 0
    primary_category = max(category_scores.items(), key=lambda x: x[1])
    return primary_category[0], primary_category[1]


@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(2))
def get_relevant_chroma_data(query: str, n_results: int = 5):
    cache_key = f"chroma:{query.lower().strip()}"
    cached = cache.get(cache_key)
    if cached:
        print("⚡ Serving ChromaDB result from cache")
        return cached

    def calculate_relevance_score(doc, query, found_categories, query_category, product_aliases, personnel_info, meta=None, distance=0.0): # Added product_aliases, meta
        """
        Calculate a weighted relevance score for a document with category focus,
        generality penalty, and service-specific boosts.
        """
        # query = normalize_query_with_aliases(query, product_aliases)
        query_lower = query.lower()
        doc_lower = doc.lower()
        query_terms = set(query_lower.split())
        doc_terms = set(doc_lower.split())
        term_overlap = len(query_terms.intersection(doc_terms)) 

        is_general_query = bool(re.match(r"what is\s+(.*?)\??$", query_lower))
        
        # --- 1. Base Score from Semantic Distance (Inverse of distance) ---
        # Max score if distance is 0, gradually decreasing. Max 10.0 for very close matches.
        # Adjust the divisor (e.g., 1.5, 2.0) to control sensitivity.
        # Higher divisor means semantic score drops off faster.
        semantic_score = max(0, (1 - (distance / 1.5)) * 10.0)

        # --- 2. Keyword/Term Overlap and Exact Matches ---
        # 'term_overlap' is already calculated.
        exact_matches = sum(1 for phrase in query_terms if phrase in doc_lower)
        term_overlap_score = term_overlap * 0.75 # Increased weight
        exact_matches_score = exact_matches * 1.0 # Increased weight

        # --- 3. Proximity Score ---
        proximity_score_raw = 0.0 # Initialize raw proximity score
        if len(query_terms) > 1:
            words = doc_lower.split()
            positions = {}
            for i, word in enumerate(words):
                for term in query_terms:
                    if term in word:
                        if term not in positions:
                            positions[term] = []
                        positions[term].append(i)

            if len(positions) > 1:
                min_distance = float('inf')
                for term1_key in positions:
                    for term2_key in positions:
                        if term1_key != term2_key:
                            for pos1 in positions[term1_key]:
                                for pos2 in positions[term2_key]:
                                    dist_val = abs(pos1 - pos2) # Renamed 'distance' to 'dist_val' to avoid confusion with function parameter
                                    min_distance = min(min_distance, dist_val)
                if min_distance != float('inf'):
                    proximity_score_raw = 1.0 / (1.0 + min_distance)
                else:
                    proximity_score_raw = 0.25 # If terms are found but too far apart or not forming a cluster

        proximity_score = proximity_score_raw * 5.0 # Scale to give more impact

        # Initialize overall score with base components
        final_score = semantic_score + term_overlap_score + exact_matches_score + proximity_score
        
        # Strong boost for exact query phrase match in document content
        if query_lower in doc_lower:
            final_score += 100.0 # Significant boost for exact phrase match
            # print(f"DEBUG: Exact query match boost applied for '{query_lower}' in doc.")
    
        # Stronger boost if exact query phrase is in the document title/metadata
        if meta and 'title' in meta and meta['title'] is not None:
            if query_lower in meta['title'].lower():
                final_score += 150.0 # Even higher boost for title match
                # print(f"DEBUG: Exact query match in title boost applied for '{query_lower}'")

        # --- 4. Category Alignment Boost ---
        # A significant boost if the document's categories align with the query's identified category
        if query_category:
            if query_category in found_categories:
                final_score += 15.0 # Strong boost for direct query category match
                if category_keywords[query_category].get('exclusive', False):
                    final_score += 5.0 # Even stronger for exclusive category match
            elif found_categories: # Smaller boost if any document category matches (but not the primary query category)
                final_score += sum(category_keywords[cat]['weight'] for cat in found_categories) * 2.0 # Use weights
                
        
        # --- 5. Targeted Entity Boosts (Personnel and Products) ---
        # These are high-impact additive boosts for specific matches,
        # conditional on the *type* of query.

        # Personnel Match Boost (if query is likely about management/personnel)
        if query_category == 'management' or any(role in query_lower for role in ["cto", "md", "ceo", "chairman", "dmd", "cro","senior executive"]):
            for person_canonical, associated_roles in personnel_info.items():
                query_mentions_person = person_canonical in query_lower
                query_mentions_role = any(role_alias.lower() in query_lower for role_alias in associated_roles)

                doc_contains_person = person_canonical in doc_lower
                doc_contains_role = any(role_alias.lower() in doc_lower for role_alias in associated_roles)

                if (query_mentions_person or query_mentions_role) and doc_contains_person and doc_contains_role:
                    # Give a very strong but non-absolute boost. This ensures it floats near the top.
                    final_score += 70.0
                    break # Apply only once

     
       # Product Match Boost
        # Ensure general_product_queries is accessible here
        is_general_product_query = any(phrase in query_lower for phrase in config.general_product_queries) 

        # Prioritize if the query is specifically about a product or if a strong product match is found
        # (even in a general query context)
        # Strong boost for exact product match to avoid "plus" variants overshadowing base queries
        normalized_query = query_lower.strip()
        product_match_boost_applied = False # This can remain or be reset here
        for alias_key, canonical_name in product_aliases.items():
            if normalized_query == alias_key.lower() or normalized_query == canonical_name.lower():
                if re.search(r'\b' + re.escape(alias_key.lower()) + r'\b', doc_lower) or \
                    re.search(r'\b' + re.escape(canonical_name.lower()) + r'\b', doc_lower):
                    final_score += 200.0  # High boost for exact match
                    product_match_boost_applied = True
                    break
            
            if not product_match_boost_applied:
                for alias_key, canonical_name in product_aliases.items():
                    if (alias_key.lower() in query_lower or canonical_name.lower() in query_lower) and \
                        (re.search(r'\b' + re.escape(canonical_name.lower()) + r'\b', doc_lower) or \
                          re.search(r'\b' + re.escape(alias_key.lower()) + r'\b', doc_lower)):
                            final_score += 100.0  # Moderate boost for partial match
                            product_match_boost_applied = True
                            break
                
                # Adjust boost based on query type or strength of match
                if query_category in ["savings", "loans", "cards", "islamic"] or is_general_product_query:
                    final_score += 60.0 # High boost for product-specific queries or if category matches
                else:
                    final_score += 40.0 # Moderate boost for product match in other contexts
                
                product_match_boost_applied = True
                break # Apply only once
        
        # Penalty for extended variant mismatch: e.g., "double benefit plus" shown for "double benefit"
        if "plus" in doc_lower and "plus" not in query_lower:
            final_score *= 0.9  # Slight demotion

        # Consider a specific boost if the title in meta contains the queried product
        # Ensure meta is not None before accessing it
        if meta and 'title' in meta:
            title_lower = meta['title'].lower()
            for alias_key, canonical_name in product_aliases.items():
                if (alias_key.lower() in query_lower or canonical_name.lower() in query_lower) and \
                   (alias_key.lower() in title_lower or canonical_name.lower() in title_lower):
                    final_score += 50.0 # Additional boost for title match
                    break # Apply only once
        
       
        compound_keywords = ["vision", "mission", "chairman", "logo", "md", "values", "green banking", "profile"]
        compound_hit_count = sum(kw in doc_lower for kw in compound_keywords)

        if compound_hit_count >= 4 and meta.get("section", "").lower() == "general":
            final_score *= 0.6  # Significant demotion
        
        
        if query_category == "management":
            if "vice chairman" in query_lower:
                if "vice chairman" not in doc_lower and "vice-chairman" not in doc_lower:
                    return max(0, final_score)  # skip chairman-only chunks

         
        if query_category == "management" and "vice chairman" in query_lower:
             if "message from chairman" in doc_lower or "chairman" in doc_lower:
                 final_score *= 0.7

            
        if meta.get("section", "").lower() == "board of directors":
            final_score += 200.0  # Strong boost for clean board chunk

        # --- 6. Sponsor Boost --
        sponsor_section = meta.get("section", "").lower()    
        applied_sponsor_boost = False
        if query_category == "sponsor":
            if any(keyword in sponsor_section for keyword in ["sponsor", "founder"]):
                final_score += 250.0
                applied_sponsor_boost = True
            elif "sponsor" in doc_lower:
                final_score += 180.0
                applied_sponsor_boost = True
        
        if query_category == "sponsor" and not applied_sponsor_boost:
            if any(kw in doc_lower for kw in ["chairman", "md", "ceo", "executive message"]):
                final_score *= 0.90


        # --- Generality Penalty for Product-Specific Content ---
        if is_general_query and query_category == 'digital': # Apply specifically for digital, or other general categories
            specific_product_mentions = 0
            canonical_product_names = set(product_aliases.values())

            for p_name in canonical_product_names:
                if re.search(rf'\b{re.escape(p_name.lower())}\b', doc_lower):
                    specific_product_mentions += 1

            if specific_product_mentions >= 3:
                final_score *= 0.5 # Substantial penalty
            elif specific_product_mentions >= 1:
                final_score *= 0.8 # Moderate penalty

        # --- Service-Specific Query Boost ---
        if any(k in query_lower for k in ["services", "what services", "list services", "service provided", "what are the services", "features of agent banking"]):
            explicit_service_phrases_in_doc = 0

            explicit_service_phrases_patterns = [
                r"what is midland online",
                r"services available",
                r"key services",
                r"list of services",
                r"special features of mdb agent banking",
                r"prohibited activities",
                r"features of agent banking",
                r"services provided by agent banking"
            ]

            for pattern in explicit_service_phrases_patterns:
                if re.search(pattern, doc_lower):
                    explicit_service_phrases_in_doc += 1

            if explicit_service_phrases_in_doc > 0:
                final_score += (explicit_service_phrases_in_doc * 7.0)

            if "prohibited" in query_lower and "prohibited activities" in doc_lower:
                final_score += 10.0

        # --- Optional: Title/Heading Boost (Requires 'meta' to be passed and contain 'title') ---
        if meta and 'title' in meta:
            title_lower = meta['title'].lower()
            if any(k in query_lower for k in ["services", "features"]) and \
               ("services available" in title_lower or "special features" in title_lower or "prohibited activities" in title_lower):
                final_score += 1.0

        for kw, bonus in bonus_keywords.items():
            if kw in doc_lower:
                final_score += bonus * 2.0
                

        # Ensure score doesn't become negative (good practice)
        return max(0, final_score)

    try:
        print(f"\n📦 Querying vector data from ChromaDB collection: {collection.name}")
        start_time = time.time()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]

        )
        end_time = time.time()
        print(f"⏱️ ChromaDB query completed in {end_time - start_time:.2f} seconds")

        all_results = []
        query_category, query_category_score = identify_query_category(query)
        print(f"\nIdentified query category: {query_category} (score: {query_category_score:.2f})")

        if results and results['documents']:
            for idx, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][idx]
                dist = results['distances'][0][idx]
                # Find matching categories
                found_categories = []
                for category, info in category_keywords.items():
                    if any(kw.lower() in doc.lower() for kw in info['keywords']):
                        found_categories.append(category)
                # Calculate relevance score with category focus
                relevance_score = calculate_relevance_score(doc, query, found_categories, query_category, product_aliases, personnel_info, meta, dist)
                # Only include results that match the query category if it's exclusive
                if query_category and category_keywords[query_category].get('exclusive', False):
                    if query_category not in found_categories and not any(
                        kw in doc.lower() for kw in ['savings', 'account', 'deposit', 'scheme']):
                        continue
                result_entry = {
                    'content': doc,
                    'score': dist,
                    'collection': collection.name,
                    'categories': found_categories,
                    'relevance_score': relevance_score
                }
                all_results.append(result_entry)

        # Sort results using the comprehensive scoring system
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        # for i, res in enumerate(all_results[:5]): # Print top 5 to see what's being prioritized
        #     print(f"Rank {i+1}: Score={res['relevance_score']:.4f}, Categories={res['categories']}, Content Preview: {res['content'][:150]}...")
        # print("-------------------------------------------------------------------")

        # Filter results to keep only the most relevant ones
        if query_category and category_keywords[query_category].get('exclusive', False):
            best_results = [r for r in all_results[:n_results] if query_category in r['categories']]
        else:
            best_results = all_results[:n_results]
            # print("\n--- DEBUG: Contents of best_results before raw_results creation ---")
            # for i, res in enumerate(best_results):
            #     print(f"Result {i+1} (Score: {res['relevance_score']:.4f}): Content Length={len(res['content'])}, Content Preview: {res['content'][:300]}...")
            # print("-------------------------------------------------------------------")

        if best_results:
            formatted_results = []
            for result in best_results:
                # For exclusive categories, only show the relevant part of the content
                if query_category == "location":
                    query_location = query.lower().strip()
                    content_lower = result['content'].lower()
                    if query_location in content_lower:
                        content = result['content']
                    else:
                        continue
                    # if any(key in result['content'].lower() for key in ["gulshan", "n. b. tower", "40/7", "dhaka"]):
                    #     content = result['content']
                    # else:
                    #     content = (
                    #         "Midland Bank Limited Head Office:\n"
                    #         "N. B. Tower (Level 6–9)\n"
                    #         "40/7 Gulshan Avenue\n"
                    #         "Gulshan-2, Dhaka-1212, Bangladesh."
                    #          )
                elif query_category and category_keywords[query_category]['exclusive']:
                    sentences = result['content'].split('.')
                    relevant_sentences = []
                    query_terms = set(query.lower().split())
                    for sentence in sentences:
                        if any(term in sentence.lower() for term in query_terms):
                            relevant_sentences.append(sentence)
                    if relevant_sentences:
                        content = '. '.join(relevant_sentences) + '.'
                    else:
                        content = result['content']
                else:
                    content = result['content']
                formatted_results.append(f"• {content}\n  [Relevance: {result['relevance_score']:.4f}]")

            # Debug log each document being passed to GPT
            # print("\n📄 Documents sent to GPT:")
            # for result in best_results:
            #     print(f"\n[Collection: {result['collection']}]")
            #     print(f"Categories: {result['categories']}")
            #     print(f"Relevance Score: {result['relevance_score']:.4f}")
            #     print("Content Preview:\n", result['content'][:500], "...\n")

            original_results = best_results.copy()
            query_lower = query.lower().strip()
            canonical_title = product_aliases.get(query_lower, "").lower()
            
            if canonical_title:
                best_results = [
                    r for r in best_results
                    if canonical_title in r.get("content", "").lower() or 
                       canonical_title in r.get("metadata", {}).get("title", "").lower()
                ]
                if not best_results:
                    print("⚠️ No matching product chunks found — reverting to original top results.")
                    best_results = original_results

            
            # ✅ Return raw results instead of formatted preview
            raw_results = [result['content'].strip() for result in best_results]
            print("\n--- DEBUG: Content of raw_results list before final join ---")
            for i, r_doc in enumerate(raw_results):
                print(f"Raw Result {i+1} (Length: {len(r_doc)}): Content Preview: {r_doc[:300]}...")
            print("-------------------------------------------------------------------")
            #print(f"Raw results {raw_results}")
            context = "\n\n".join(raw_results)
            cache[cache_key] = context
            # print(f"\n--- DEBUG: FINAL context sent to GPT (first 1000 chars) ---")
            # print(context[:6000])
            # print("-----------------------------------------------------------")
            return context


        return "No relevant information found in the bank's knowledge base."

    except Exception as e:
        print(f"ChromaDB Error: {str(e)}")
        return "Error accessing the knowledge base."

def inspect_chroma_collections():
    """Inspect ChromaDB collections and their metadata"""
    try:
        collections = [collection]
        print("\n=== ChromaDB Collections Information ===")
        for coll in collections:
            print(f"\nCollection Name: {collection.name}")
            print(f"Number of documents: {collection.count()}")
            # Get collection metadata if any
            try:
                peek = collection.peek()
                if peek and peek['documents']:
                    print("Sample document:", peek['documents'][0][:200], "...")
            except Exception as e:
                print(f"Error peeking collection: {str(e)}")
    except Exception as e:
        print(f"Error inspecting collections: {str(e)}")
