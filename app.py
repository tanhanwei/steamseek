from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import Markup
import os
import json
import logging
import markdown  # pip install markdown

# Import our data loader and helper functions
from data_loader import build_steam_data_index, load_summaries, get_game_data_by_appid
from game_chatbot import semantic_search_query
from llm_processor import generate_game_analysis, rerank_search_results, OPENROUTER_API_KEY, optimize_search_query

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Required for session support

# --- Explicit Logger Configuration ---
# Remove existing basicConfig if it causes conflicts, or adjust level
# logging.basicConfig(level=logging.INFO) # Keep or remove based on testing
if not app.debug: # Optionally configure differently for production
    # Example: Log to a file in production
    # handler = logging.FileHandler('app.log')
    # handler.setLevel(logging.INFO)
    # app.logger.addHandler(handler)
    pass 
else:
     # Ensure logger level is set for debug mode
    app.logger.setLevel(logging.INFO)
app.logger.info("Flask logger initialized with level: %s", app.logger.getEffectiveLevel())

# Check OpenRouter API Key
if not OPENROUTER_API_KEY:
    print("\n===========================================================")
    print("WARNING: OPENROUTER_API_KEY not set in .env file")
    print("LLM re-ranking will not work without a valid API key")
    print("===========================================================\n")
else:
    print(f"\nOpenRouter API Key found (masked): {OPENROUTER_API_KEY[:4]}...{OPENROUTER_API_KEY[-4:]}")
# ------------------------------------

# Custom Jinja filter to render markdown as HTML
def markdown_filter(text):
    return Markup(markdown.markdown(text))
app.jinja_env.filters['markdown'] = markdown_filter

# Define file paths
STEAM_DATA_FILE = "data/steam_games_data.jsonl"
SUMMARIES_FILE = "data/summaries.jsonl"  # Pre-run AI summaries for semantic search
ANALYSIS_CACHE_FILE = "data/analysis_cache.jsonl"  # Detailed analysis cache for dashboard

# TESTING flag for development - set to True to enable synthetic summaries for testing
TESTING_ENABLE_SYNTHETIC_SUMMARIES = True

# Build the index map once at startup
logging.basicConfig(level=logging.INFO)
index_map = build_steam_data_index(STEAM_DATA_FILE)

def force_https(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[7:]
    return url

#############################################
# Analysis Cache Helper Functions
#############################################
def load_analysis_cache(file_path: str) -> dict:
    """Load the detailed analysis cache from an external file."""
    cache = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    appid = obj.get("appid")
                    if appid is not None:
                        cache[int(appid)] = obj
                except Exception as e:
                    app.logger.warning(f"Error parsing analysis cache line: {e}")
    return cache

def save_analysis_cache(cache: dict, file_path: str):
    """Save the detailed analysis cache to an external file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for analysis in cache.values():
                f.write(json.dumps(analysis) + "\n")
    except Exception as e:
        app.logger.error(f"Error saving analysis cache: {e}")

#############################################
# Search Helper with Filtering and Sorting
#############################################
def perform_search(query, selected_genre="All", selected_year="All", selected_platform="All", selected_price="All", sort_by="Relevance", use_ai_enhanced=False):
    app.logger.info(f"--- Entering perform_search --- Query: '{query}', Sort By: '{sort_by}', AI Enhanced: {use_ai_enhanced}") # DEBUG
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
        app.logger.info("Semantic search returned no results.") # DEBUG
        return [], optimization_explanation
    else:
        app.logger.info(f"Semantic search returned {len(raw_results)} raw results.") # DEBUG
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
    app.logger.info(f"Prepared {len(candidates_for_reranking)} candidates for re-ranking (limit: {limit_for_reranking}).")

    # 3. Determine the processing order of appids
    processing_order_appids = original_semantic_order_appids # Default: semantic order

    # --- DEBUG Check before IF ---
    app.logger.info(f"Checking condition for re-ranking: sort_by == 'Relevance' ({sort_by == 'Relevance'}), len(candidates_for_reranking) > 0 ({len(candidates_for_reranking) > 0})")
    # --- END DEBUG ---

    if sort_by == "Relevance" and candidates_for_reranking:
        app.logger.info(f"Attempting LLM re-ranking for query: '{actual_search_query}'") # Expected log
        print(f"\n>> ATTEMPTING LLM RE-RANKING for query: '{actual_search_query}'")
        print(f">> Number of candidates: {len(candidates_for_reranking)}")
        
        try:
            # Before calling the function
            print(f">> First few candidate AppIDs: {[c['appid'] for c in candidates_for_reranking[:3]]}")
            print(">> First candidate summary (truncated): " + candidates_for_reranking[0]['ai_summary'][:100] + "...")
            
            # Call the new re-ranking function
            app.logger.info("Calling rerank_search_results...") # DEBUG
            print(">> Calling rerank_search_results function now...")
            
            ordered_appids_from_llm, llm_comment = rerank_search_results(actual_search_query, candidates_for_reranking)
            
            app.logger.info("rerank_search_results call completed.") # DEBUG
            print(">> rerank_search_results call completed.")

            if ordered_appids_from_llm is not None:
                app.logger.info(f"LLM Re-ranking successful. Comment: {llm_comment}") # Expected log
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
                 app.logger.warning(f"LLM re-ranking failed or returned invalid data. Reason: {llm_comment}. Falling back to semantic order.") # Expected log
                 print(f">> FAILURE: {llm_comment}")
                 print(">> Falling back to semantic search order.")
                 # Keep the default semantic order assigned earlier
        except Exception as e:
            app.logger.error(f"Exception during LLM re-ranking call: {e}. Falling back to semantic order.", exc_info=True) # Expected log
            print(f">> EXCEPTION: {e}")
            import traceback
            print(traceback.format_exc())
            print(">> Falling back to semantic search order.")
            # Keep the default semantic order assigned earlier
        
        print(">> LLM RE-RANKING ATTEMPT COMPLETE")
    else:
        app.logger.info("Skipping LLM re-ranking based on sort_by or empty candidates.") # DEBUG
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
            app.logger.warning(f"Could not retrieve game data for appid {appid} during search processing.")
            continue

        # --- Extract data needed for filtering and display (reuse existing logic) ---
        reviews = game_data.get("reviews", [])
        total_reviews = len(reviews)
        positive_count = sum(1 for review in reviews if review.get("voted_up"))
        pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

        media = [] # Extract media... (keep existing logic)
        if game_data.get("header_image"): media.append(force_https(game_data["header_image"]))
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
             try: year = release_date_str.split(",")[-1].strip()
             except: pass

        platforms = game_data.get("store_data", {}).get("platforms", {}) # Extract platforms...

        is_free = game_data.get("store_data", {}).get("is_free", False) # Extract price...
        price = 0.0
        if not is_free:
             price_overview = game_data.get("store_data", {}).get("price_overview", {})
             if price_overview: price = price_overview.get("final", 0) / 100.0

        # --- Apply Filters ---
        if selected_genre != "All" and selected_genre not in genres: continue
        if selected_year != "All" and year != selected_year: continue
        if selected_platform != "All":
            platform_key = selected_platform.lower()
            if not platforms.get(platform_key, False): continue
        if selected_price == "Free" and not is_free: continue
        if selected_price == "Paid" and is_free: continue

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
        app.logger.info(f"Applying final sort: {sort_by}")
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

    # Optional: Limit the number of results returned to the template
    # final_results = final_results[:max_results_to_display]

    app.logger.info(f"--- Exiting perform_search --- Returning {len(final_results)} final results.") # DEBUG
    return final_results, optimization_explanation

#############################################
# Routes
#############################################
@app.route("/", methods=["GET", "POST"])
def search():
    query = ""
    results = []
    optimization_explanation = ""
    # Default filter values
    selected_genre = "All"
    selected_year = "All"
    selected_platform = "All"
    selected_price = "All"
    sort_by = "Relevance"
    use_ai_enhanced = False
    show_previous_search = False

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        selected_genre = request.form.get("genre", "All")
        selected_year = request.form.get("release_year", "All")
        selected_platform = request.form.get("platform", "All")
        selected_price = request.form.get("price", "All")
        sort_by = request.form.get("sort_by", "Relevance")
        use_ai_enhanced = request.form.get("use_ai_enhanced") == "true"  # Convert string to boolean

        if query:
            results, optimization_explanation = perform_search(
                query, 
                selected_genre, 
                selected_year, 
                selected_platform, 
                selected_price, 
                sort_by,
                use_ai_enhanced
            )
            # Store only search parameters and not the full results to keep cookie size small
            session["last_search"] = {
                "query": query,
                # Don't store results in the session to avoid large cookies
                "filters": {
                    "genre": selected_genre,
                    "release_year": selected_year,
                    "platform": selected_platform,
                    "price": selected_price,
                    "sort_by": sort_by,
                    "use_ai_enhanced": use_ai_enhanced
                }
            }
        else:
            session.pop("last_search", None)
    elif request.method == "GET":
        # Handle explicit query parameters in URL
        query = request.args.get("q", "").strip()
        selected_genre = request.args.get("genre", "All")
        selected_year = request.args.get("release_year", "All")
        selected_platform = request.args.get("platform", "All")
        selected_price = request.args.get("price", "All")
        sort_by = request.args.get("sort_by", "Relevance")
        use_ai_enhanced = request.args.get("use_ai_enhanced") == "true"
        # Flag to explicitly re-run search (not set by default)
        run_search = request.args.get("run_search") == "true"

        if query and run_search:
            # Only execute search if query is provided AND run_search flag is set
            results, optimization_explanation = perform_search(
                query, 
                selected_genre, 
                selected_year, 
                selected_platform, 
                selected_price, 
                sort_by,
                use_ai_enhanced
            )
            # Store parameters in session
            session["last_search"] = {
                "query": query,
                "filters": {
                    "genre": selected_genre,
                    "release_year": selected_year,
                    "platform": selected_platform,
                    "price": selected_price,
                    "sort_by": sort_by,
                    "use_ai_enhanced": use_ai_enhanced
                }
            }
        elif "last_search" in session and not query:
            # If there's a previous search in session and no new query provided,
            # just restore the previous search parameters (don't re-run the search)
            cached = session["last_search"]
            query = cached.get("query", "")
            if query:
                filters = cached.get("filters", {})
                selected_genre = filters.get("genre", "All")
                selected_year = filters.get("release_year", "All")
                selected_platform = filters.get("platform", "All")
                selected_price = filters.get("price", "All")
                sort_by = filters.get("sort_by", "Relevance")
                use_ai_enhanced = filters.get("use_ai_enhanced", False)
                show_previous_search = True
                
                # Only show this message when we're displaying a previous search form
                if show_previous_search:
                    optimization_explanation = "Your previous search is ready to run again"

    return render_template("search.html", 
                          query=query, 
                          results=results,
                          selected_genre=selected_genre, 
                          selected_year=selected_year,
                          selected_platform=selected_platform, 
                          selected_price=selected_price,
                          sort_by=sort_by,
                          use_ai_enhanced=use_ai_enhanced,
                          optimization_explanation=optimization_explanation,
                          show_previous_search=show_previous_search)

@app.route("/detail/<appid>")
def detail(appid):
    try:
        appid_int = int(appid)
    except ValueError:
        return "Invalid AppID", 400

    # Preserve original search query so that the "Back to Search" link works
    orig_query = request.args.get("q", "")
    # Check if user requested a refresh ("Analyze Again")
    refresh = request.args.get("refresh", "0")

    game_data = get_game_data_by_appid(appid_int, STEAM_DATA_FILE, index_map)
    if not game_data:
        return "Game not found", 404

    # Load the external analysis cache (separate from summaries.jsonl)
    analysis_cache = load_analysis_cache(ANALYSIS_CACHE_FILE)

    # Define required keys for a complete analysis
    required_keys = {"ai_summary", "feature_sentiment", "standout_features",
                     "community_feedback", "market_analysis", "feature_validation"}
    analysis_obj = analysis_cache.get(appid_int)

    if refresh == "1" or not analysis_obj or not required_keys.issubset(analysis_obj.keys()):
        app.logger.info("Generating new detailed analysis via LLM...")
        analysis = generate_game_analysis(game_data)
        # Ensure the analysis object contains the appid for later retrieval
        analysis["appid"] = appid_int
        analysis_cache[appid_int] = analysis
        # Save updated analysis cache externally
        save_analysis_cache(analysis_cache, ANALYSIS_CACHE_FILE)
    else:
        analysis = analysis_obj

    # Compute metrics from raw reviews
    reviews = game_data.get("reviews", [])
    total_reviews = len(reviews)
    positive_count = sum(1 for r in reviews if r.get("voted_up"))
    pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

    # Build playtime distribution
    playtime_buckets = {"<10h": 0, "10-50h": 0, "50-100h": 0, ">100h": 0}
    for r in reviews:
        hours = r.get("playtime_forever", 0) / 60
        if hours < 10:
            playtime_buckets["<10h"] += 1
        elif hours < 50:
            playtime_buckets["10-50h"] += 1
        elif hours < 100:
            playtime_buckets["50-100h"] += 1
        else:
            playtime_buckets[">100h"] += 1
    playtime_distribution = [{"name": k, "value": v} for k, v in playtime_buckets.items()]

    # Player growth data (fallback if not available)
    player_growth = game_data.get("player_growth")
    if not player_growth or not isinstance(player_growth, list):
        player_growth = [
            {"month": "Jan", "players": 125},
            {"month": "Feb", "players": 350},
            {"month": "Mar", "players": 410},
            {"month": "Apr", "players": 380},
            {"month": "May", "players": 425},
        ]
        player_growth_available = False
    else:
        player_growth_available = True

    # Compute media list for carousel (same as in search)
    media = []
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

    return render_template("detail.html",
                           game=game_data,
                           analysis=analysis,
                           pos_percent=pos_percent,
                           total_reviews=total_reviews,
                           playtime_distribution=playtime_distribution,
                           player_growth=player_growth,
                           player_growth_available=player_growth_available,
                           orig_query=orig_query,
                           media=media)

if __name__ == "__main__":
    # Make sure debug is True for development logging
    app.run(debug=True, threaded=True)
