from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
import time
import uuid
from threading import Thread
from collections import OrderedDict

# Import necessary modules for search functionality
from data_loader import get_game_data_by_appid, load_summaries
from game_chatbot import semantic_search_query
from llm_processor import (rerank_search_results, optimize_search_query, 
                          deep_search_generate_variations, deep_search_generate_summary)

# Create the blueprint
search_bp = Blueprint('search', __name__, template_folder='templates')

# Global search state variables 
# These will need to be moved to a proper background task queue in later refactoring
regular_search_status = {
    "active": False,
    "progress": 0,
    "current_step": "",
    "results": [],
    "completed": False,
    "error": None,
    "session_id": None
}

deep_search_status = {
    "active": False,
    "progress": 0,
    "total_steps": 0,
    "current_step": "",
    "results": [],
    "grand_summary": "",
    "original_query": "",
    "completed": False,
    "error": None,
    "session_id": None,
    "results_served": False
}

# Helper function for force HTTPS
def force_https(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[7:]
    return url

# Helper functions for search processing
def perform_search(query, selected_genre="All", selected_year="All", selected_platform="All", 
                  selected_price="All", sort_by="Relevance", use_ai_enhanced=False, 
                  use_deep_search=False, save_to_status=True, limit=50):
    """
    Perform a search query with optional filters and sorting
    """
    current_app.logger.info(f"--- Entering perform_search --- Query: '{query}', Sort By: '{sort_by}', AI Enhanced: {use_ai_enhanced}, Deep Search: {use_deep_search}")
    
    # Define file paths
    SUMMARIES_FILE = "data/summaries.jsonl"
    STEAM_DATA_FILE = "data/steam_games_data.jsonl"
    TESTING_ENABLE_SYNTHETIC_SUMMARIES = True
    
    # Get the index_map from the Flask app
    index_map = current_app.config.get('index_map')
    
    # Make sure the query is properly stripped of whitespace
    query = query.strip()
    
    # If limit is None, set it to a default of 50
    if limit is None:
        limit = 50
    
    # If requesting a deep search, we'll start the background process and return empty results
    if use_deep_search:
        global deep_search_status
        
        # Check if we already have a completed deep search for this query that hasn't been served
        if deep_search_status["completed"] and not deep_search_status["results_served"] and deep_search_status["original_query"].lower() == query.lower():
            # Use the completed deep search results instead of starting a new search
            print(f"Using existing completed deep search results for query: '{query}'")
            return deep_search_status["results"], "Deep Search completed. Here are your results."
        
        # If a deep search is already running, just return empty results
        if deep_search_status["active"]:
            return [], "A Deep Search is already in progress."
        
        # Check if this is a restart of an identical search
        if deep_search_status["completed"] and deep_search_status["original_query"].lower() == query.lower():
            print(f"Preventing automatic restart of deep search for: '{query}'")
            return [], "This search was already completed. Refresh the page to start a new deep search."
        
        # Reset deep search status with a completely new dictionary to prevent partial updates
        deep_search_status.clear()
        deep_search_status.update({
            "active": True,
            "progress": 0,
            "total_steps": 0,
            "current_step": "Initializing Deep Search",
            "results": [],
            "grand_summary": "",
            "original_query": query,  # Set the original query
            "completed": False,
            "error": None,
            "session_id": None,  # Will be set in the background task
            "results_served": False  # Reset the served flag
        })
        
        print(f"Initialized new deep search for: '{query}'")
        
        # Start the background task
        search_params = {
            "genre": selected_genre,
            "year": selected_year,
            "platform": selected_platform,
            "price": selected_price,
        }
        thread = Thread(target=deep_search_background_task, args=(query, search_params))
        thread.daemon = True
        thread.start()
        
        # Return empty results - the client will poll for updates
        return [], "Deep Search started. Please wait while we find the best results for you."
    
    # Regular search process
    summaries_dict = load_summaries(SUMMARIES_FILE)
    print(f"Perform search loaded {len(summaries_dict)} summaries") # NEW DEBUG
    
    # Apply AI optimization to the query if enabled
    actual_search_query = query
    optimization_explanation = ""
    
    if use_ai_enhanced and query.strip():
        try:
            actual_search_query, optimization_explanation = optimize_search_query(query)
            print(f"Original query: '{query}'")
            print(f"Optimized query: '{actual_search_query}'")
            print(f"Explanation: {optimization_explanation}")
        except Exception as e:
            print(f"Error optimizing query: {e}")
            # Fall back to original query if optimization fails
            pass
    
    # 1. Get initial semantic search results using the actual search query
    initial_top_k = 50
    limit_for_reranking = 50 # Changed from 25 to 50 games for re-ranking
    raw_results = semantic_search_query(actual_search_query, top_k=initial_top_k)

    if not raw_results:
        current_app.logger.info("Semantic search returned no results.") # DEBUG
        return [], optimization_explanation
    else:
        current_app.logger.info(f"Semantic search returned {len(raw_results)} raw results.") # DEBUG
        # NEW DEBUG - Show a sample of the raw results
        if len(raw_results) > 0:
            sample = raw_results[0]
            print(f"Sample raw result: appid={sample.get('appid')}, name={sample.get('name')}")

    # 2. Prepare candidates for potential LLM re-ranking and track original order
    candidates_for_reranking = []
    original_semantic_order_appids = []
    missing_summaries_count = 0
    
    for r in raw_results:
        appid = r.get("appid")
        if not appid: continue
        appid_int = int(appid)
        original_semantic_order_appids.append(appid_int)
        # Prepare candidate only if it's within the limit we send to the LLM
        if len(candidates_for_reranking) < limit_for_reranking:
             # Get the actual game data to access more information if needed
             game_data = None
             if TESTING_ENABLE_SYNTHETIC_SUMMARIES:
                 game_data = get_game_data_by_appid(appid_int, STEAM_DATA_FILE, index_map)
             
             summary_obj = summaries_dict.get(appid_int, {})
             ai_summary = summary_obj.get("ai_summary", "")
             
             if ai_summary:
                 # We have a real AI summary from the summaries file
                 candidates_for_reranking.append({"appid": appid_int, "ai_summary": ai_summary})
             elif TESTING_ENABLE_SYNTHETIC_SUMMARIES and game_data:
                 # TESTING MODE: Generate a synthetic summary for testing
                 missing_summaries_count += 1
                 
                 # Create a basic description from the game data
                 name = game_data.get("name", "Unknown Game")
                 description = game_data.get("short_description", "No description available.")
                 
                 # Create a synthetic summary that's good enough for testing
                 synthetic_summary = f"SYNTHETIC SUMMARY FOR TESTING:\n{name} is a game on Steam. {description}"
                 
                 if missing_summaries_count <= 3:
                     print(f"Generated synthetic summary for: {name} (appid: {appid_int})")
                 
                 candidates_for_reranking.append({
                     "appid": appid_int, 
                     "ai_summary": synthetic_summary
                 })
             else:
                 missing_summaries_count += 1
                 # Only print the first few missing ones to avoid console spam
                 if missing_summaries_count <= 5:
                     print(f"Missing AI summary for appid {appid_int} (name: {r.get('name', 'Unknown')})")

    print(f"Missing summaries for {missing_summaries_count} out of {len(original_semantic_order_appids)} search results")
    print(f"Final candidate count for re-ranking: {len(candidates_for_reranking)}")
    current_app.logger.info(f"Prepared {len(candidates_for_reranking)} candidates for re-ranking (limit: {limit_for_reranking}).")

    # 3. Determine the processing order of appids
    processing_order_appids = original_semantic_order_appids # Default: semantic order

    # --- DEBUG Check before IF ---
    current_app.logger.info(f"Checking condition for re-ranking: sort_by == 'Relevance' ({sort_by == 'Relevance'}), len(candidates_for_reranking) > 0 ({len(candidates_for_reranking) > 0})")
    # --- END DEBUG ---

    if sort_by == "Relevance" and candidates_for_reranking:
        current_app.logger.info(f"Attempting LLM re-ranking for query: '{actual_search_query}'") # Expected log
        print(f"\n>> ATTEMPTING LLM RE-RANKING for query: '{actual_search_query}'")
        print(f">> Number of candidates: {len(candidates_for_reranking)}")
        
        try:
            # Before calling the function
            print(f">> First few candidate AppIDs: {[c['appid'] for c in candidates_for_reranking[:3]]}")
            print(">> First candidate summary (truncated): " + candidates_for_reranking[0]['ai_summary'][:100] + "...")
            
            # Call the new re-ranking function
            current_app.logger.info("Calling rerank_search_results...") # DEBUG
            print(">> Calling rerank_search_results function now...")
            
            ordered_appids_from_llm, llm_comment = rerank_search_results(actual_search_query, candidates_for_reranking)
            
            current_app.logger.info("rerank_search_results call completed.") # DEBUG
            print(">> rerank_search_results call completed.")

            if ordered_appids_from_llm is not None:
                current_app.logger.info(f"LLM Re-ranking successful. Comment: {llm_comment}") # Expected log
                print(f">> SUCCESS! LLM comment: {llm_comment}")
                
                # Create the new order: Start with LLM's order, then append remaining semantic results
                # that weren't in the LLM's list, maintaining their relative semantic order.
                llm_ordered_set = set(ordered_appids_from_llm)
                # Append remaining original IDs not covered by LLM ranking
                remaining_semantic_appids = [appid for appid in original_semantic_order_appids if appid not in llm_ordered_set]
                processing_order_appids = ordered_appids_from_llm + remaining_semantic_appids
                
                print(f">> New processing order (first few): {processing_order_appids[:5]}")
            else:
                 # Re-ranking failed, log the reason (comment might contain error)
                 current_app.logger.warning(f"LLM re-ranking failed or returned invalid data. Reason: {llm_comment}. Falling back to semantic order.") # Expected log
                 print(f">> FAILURE: {llm_comment}")
                 print(">> Falling back to semantic search order.")
                 # Keep the default semantic order assigned earlier
        except Exception as e:
            current_app.logger.error(f"Exception during LLM re-ranking call: {e}. Falling back to semantic order.", exc_info=True) # Expected log
            print(f">> EXCEPTION: {e}")
            import traceback
            print(traceback.format_exc())
            print(">> Falling back to semantic search order.")
            # Keep the default semantic order assigned earlier
        
        print(">> LLM RE-RANKING ATTEMPT COMPLETE")
    else:
        current_app.logger.info("Skipping LLM re-ranking based on sort_by or empty candidates.") # DEBUG
        print(f">> Skipping LLM re-ranking. sort_by={sort_by}, candidates={len(candidates_for_reranking)}")

    # 4. Fetch full data, filter, and build results based on the determined processing_order_appids
    results_dict = {} # Use dict to store results before final sorting
    processed_count = 0
    max_results_to_display = 25 # Limit final results shown on page? Adjust as needed.

    for appid in processing_order_appids:
        # Optional: Stop processing if we have enough results for the page
        # if processed_count >= max_results_to_display:
        #    break

        # --- Fetch full game data ---
        game_data = get_game_data_by_appid(appid, STEAM_DATA_FILE, index_map)
        if not game_data:
            current_app.logger.warning(f"Could not retrieve game data for appid {appid} during search processing.")
            continue

        # --- Extract data needed for filtering and display (reuse existing logic) ---
        reviews = game_data.get("reviews", [])
        total_reviews = len(reviews)
        positive_count = sum(1 for review in reviews if review.get("voted_up"))
        pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

        media = [] # Extract media... (keep existing logic)
        if game_data.get("header_image"): 
            media.append(force_https(game_data["header_image"]))
        if isinstance(game_data.get("screenshots"), list):
            for s in game_data["screenshots"]:
                if isinstance(s, dict) and s.get("path_full"):
                    media.append(force_https(s["path_full"]))
                else:
                    media.append(force_https(str(s)))
        store_data = game_data.get("store_data", {})
        if isinstance(store_data, dict):
            movies = store_data.get("movies", [])
            for movie in movies:
                webm_max = movie.get("webm", {}).get("max")
                mp4_max = movie.get("mp4", {}).get("max")
                if webm_max:
                    media.append(force_https(webm_max))
                elif mp4_max:
                    media.append(force_https(mp4_max))
                else:
                    thumb = movie.get("thumbnail")
                    if thumb:
                        media.append(force_https(thumb))

        summary_obj = summaries_dict.get(appid, {}) # Fetch summary again or pass from raw_results if needed
        ai_summary = summary_obj.get("ai_summary", "")

        genres = [] # Extract genres... (keep existing logic)
        if "store_data" in game_data and isinstance(game_data["store_data"], dict):
            genre_list = game_data["store_data"].get("genres", [])
            genres = [g.get("description") for g in genre_list if g.get("description")]

        release_date_str = game_data.get("release_date", "") # Extract year... (keep existing logic)
        year = "Unknown"
        if release_date_str:
            try: 
                year = release_date_str.split(",")[-1].strip()
            except: 
                pass

        platforms = game_data.get("store_data", {}).get("platforms", {}) # Extract platforms...

        is_free = game_data.get("store_data", {}).get("is_free", False) # Extract price...
        price = 0.0
        if not is_free:
            price_overview = game_data.get("store_data", {}).get("price_overview", {})
            if price_overview: 
                price = price_overview.get("final", 0) / 100.0

        # --- Apply Filters ---
        if selected_genre != "All" and selected_genre not in genres: 
            continue
        if selected_year != "All" and year != selected_year: 
            continue
        if selected_platform != "All":
            platform_key = selected_platform.lower()
            if not platforms.get(platform_key, False): 
                continue
        if selected_price == "Free" and not is_free: 
            continue
        if selected_price == "Paid" and is_free: 
            continue

        # --- If filters pass, store the result ---
        results_dict[appid] = {
            "appid": appid,
            "name": game_data.get("name", "Unknown"),
            "media": media,
            "genres": genres,
            "release_year": year,
            "platforms": platforms,
            "is_free": is_free,
            "price": price,
            "pos_percent": pos_percent,
            "total_reviews": total_reviews,
            "ai_summary": ai_summary # Keep summary for potential display
        }
        processed_count += 1

    # 5. Create the final list, respecting the processing order
    # This ensures that if sort_by=="Relevance", the LLM/semantic order is maintained after filtering
    final_results = [results_dict[appid] for appid in processing_order_appids if appid in results_dict]

    # 6. Apply final explicit sorting ONLY if the user chose something other than "Relevance"
    if sort_by != "Relevance":
        current_app.logger.info(f"Applying final sort: {sort_by}")
        if sort_by == "Name (A-Z)":
            final_results.sort(key=lambda x: x["name"])
        elif sort_by == "Release Date (Newest)":
            final_results.sort(key=lambda x: int(x["release_year"]) if x["release_year"].isdigit() else 0, reverse=True)
        elif sort_by == "Release Date (Oldest)":
            final_results.sort(key=lambda x: int(x["release_year"]) if x["release_year"].isdigit() else float('inf'))
        elif sort_by == "Price (Low to High)":
            final_results.sort(key=lambda x: x["price"])
        elif sort_by == "Price (High to Low)":
            final_results.sort(key=lambda x: x["price"], reverse=True)
        elif sort_by == "Review Count (High to Low)":
            final_results.sort(key=lambda x: x["total_reviews"], reverse=True)
        elif sort_by == "Positive Review % (High to Low)":
            final_results.sort(key=lambda x: x["pos_percent"], reverse=True)

    # Limit the final results based on the user's selection
    if limit and limit < len(final_results):
        current_app.logger.info(f"Limiting final results from {len(final_results)} to {limit}")
        final_results = final_results[:limit]

    # If this is a deep search and we need to save to status
    if save_to_status and use_deep_search:
        deep_search_status["results"] = final_results

    current_app.logger.info(f"--- Exiting perform_search --- Returning {len(final_results)} final results.") # DEBUG
    return final_results, optimization_explanation

# Deep search background process
def deep_search_background_task(query, search_params):
    """
    Background task for processing deep search queries
    """
    global deep_search_status
    
    # Store the original query for reference and later matching
    original_query = query.strip()
    
    # Generate a unique session ID for this search
    session_id = str(uuid.uuid4())
    deep_search_status["session_id"] = session_id
    deep_search_status["original_query"] = original_query  # Make sure to set this explicitly
    
    # This function will be implemented later with the actual task processing code
    # For now, just simulate progress
    try:
        print(f"\n==== STARTING DEEP SEARCH FOR: '{original_query}' (Session: {session_id}) ====\n")
        deep_search_status["current_step"] = "Placeholder deep search processing"
        deep_search_status["progress"] = 100
        deep_search_status["completed"] = True
        deep_search_status["active"] = False
        deep_search_status["results"] = []
        deep_search_status["grand_summary"] = "Deep search implementation will be completed in the next step"
    except Exception as e:
        deep_search_status["error"] = str(e)
        deep_search_status["progress"] = 100
        deep_search_status["completed"] = True
        deep_search_status["active"] = False

# Regular search background process
def regular_search_background_task(query, search_params):
    """
    Background task for processing AI-enhanced search queries
    """
    # This function will be implemented later
    pass

# Routes for search functionality
@search_bp.route('/')
@search_bp.route('/search')
def search_page():
    """
    Main search page
    """
    return render_template('search.html')

@search_bp.route('/search_status')
def check_search_status():
    """
    API endpoint to check the status of an ongoing search
    """
    global regular_search_status
    return jsonify(regular_search_status)

@search_bp.route('/deep_search_status')
def check_deep_search_status():
    """
    API endpoint to check the status of an ongoing deep search
    """
    global deep_search_status
    
    status_copy = dict(deep_search_status)  # Make a copy to avoid thread issues
    
    # Ensure all necessary fields are present
    if "progress" not in status_copy:
        status_copy["progress"] = 0
    
    if "current_step" not in status_copy:
        status_copy["current_step"] = "Initializing..."
    
    if "completed" not in status_copy:
        status_copy["completed"] = False
    
    # Add a client_friendly field to indicate search is ready for viewing
    status_copy["ready_for_viewing"] = status_copy.get("completed", False) and not status_copy.get("results_served", False)
    
    # For security/performance reasons, don't include the full results
    # in the status JSON (they can be large)
    if "results" in status_copy:
        # Just include the count instead of the full results
        status_copy["result_count"] = len(status_copy["results"])
        del status_copy["results"]
    
    # Print status when a search is ready for viewing
    if status_copy["ready_for_viewing"]:
        print(f"Deep search is ready for viewing: query='{status_copy.get('original_query', '')}', result_count={status_copy.get('result_count', 0)}")
    
    return jsonify(status_copy)

# Implement the search route
@search_bp.route('/search/execute', methods=['POST'])
def execute_search():
    """
    Process a search form submission
    """
    query = request.form.get('query', '').strip()
    genre = request.form.get('genre', 'All')
    year = request.form.get('year', 'All')
    platform = request.form.get('platform', 'All')
    price = request.form.get('price', 'All')
    sort_by = request.form.get('sort_by', 'Relevance')
    use_ai_enhanced = request.form.get('use_ai_enhanced') == 'on'
    use_deep_search = request.form.get('use_deep_search') == 'on'
    result_limit = request.form.get('result_limit', '50')
    
    try:
        result_limit = int(result_limit)
    except ValueError:
        result_limit = 50
    
    results, explanation = perform_search(
        query, genre, year, platform, price, sort_by,
        use_ai_enhanced, use_deep_search, True, result_limit
    )
    
    return render_template(
        'search_results_partial.html',
        results=results,
        query=query,
        explanation=explanation,
        use_deep_search=use_deep_search
    ) 