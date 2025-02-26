from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import Markup
import os
import json
import logging
import markdown  # pip install markdown

# Import our data loader and helper functions
from data_loader import build_steam_data_index, load_summaries, get_game_data_by_appid
from game_chatbot import semantic_search_query
from llm_processor import generate_game_analysis

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Required for session support

# Custom Jinja filter to render markdown as HTML
def markdown_filter(text):
    return Markup(markdown.markdown(text))
app.jinja_env.filters['markdown'] = markdown_filter

# Define file paths
STEAM_DATA_FILE = "data/steam_games_data.jsonl"
SUMMARIES_FILE = "data/summaries.jsonl"  # Pre-run AI summaries for semantic search
ANALYSIS_CACHE_FILE = "data/analysis_cache.jsonl"  # Detailed analysis cache for dashboard

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
# Search Route (uses pre-run summaries for semantic search)
#############################################
@app.route("/", methods=["GET", "POST"])
def search():
    query = ""
    results = []

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            # Run semantic search and build results
            summaries_dict = load_summaries(SUMMARIES_FILE)
            raw_results = semantic_search_query(query, top_k=20)
            if raw_results:
                for r in raw_results:
                    appid = r.get("appid")
                    if not appid:
                        continue
                    game_data = get_game_data_by_appid(int(appid), STEAM_DATA_FILE, index_map)
                    if not game_data:
                        continue

                    reviews = game_data.get("reviews", [])
                    total_reviews = len(reviews)
                    positive_count = sum(1 for review in reviews if review.get("voted_up"))
                    pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

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

                    summary_obj = summaries_dict.get(int(appid), {})
                    ai_summary = summary_obj.get("ai_summary", "")

                    results.append({
                        "appid": appid,
                        "name": game_data.get("name", "Unknown"),
                        "media": media,
                        "tags": [g.get("description") for g in game_data.get("genres", []) if g.get("description")],
                        "pos_percent": pos_percent,
                        "total_reviews": total_reviews,
                        "ai_summary": ai_summary
                    })
            # Cache the query and its results in session
            session["last_search"] = {"query": query, "results": results}
        else:
            session.pop("last_search", None)
    elif request.method == "GET":
        # Check for query parameter; if empty, use cached search from session
        query = request.args.get("q", "").strip()
        if not query and "last_search" in session:
            cached = session["last_search"]
            query = cached.get("query", "")
            results = cached.get("results", [])
        elif query:
            # If a query is passed via URL, check if it matches the cached query
            cached = session.get("last_search", {})
            if cached.get("query", "") == query:
                results = cached.get("results", [])
            else:
                # Otherwise, run a fresh search (and update session)
                summaries_dict = load_summaries(SUMMARIES_FILE)
                raw_results = semantic_search_query(query, top_k=20)
                if raw_results:
                    for r in raw_results:
                        appid = r.get("appid")
                        if not appid:
                            continue
                        game_data = get_game_data_by_appid(int(appid), STEAM_DATA_FILE, index_map)
                        if not game_data:
                            continue

                        reviews = game_data.get("reviews", [])
                        total_reviews = len(reviews)
                        positive_count = sum(1 for review in reviews if review.get("voted_up"))
                        pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

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

                        summary_obj = summaries_dict.get(int(appid), {})
                        ai_summary = summary_obj.get("ai_summary", "")

                        results.append({
                            "appid": appid,
                            "name": game_data.get("name", "Unknown"),
                            "media": media,
                            "tags": [g.get("description") for g in game_data.get("genres", []) if g.get("description")],
                            "pos_percent": pos_percent,
                            "total_reviews": total_reviews,
                            "ai_summary": ai_summary
                        })
                session["last_search"] = {"query": query, "results": results}

    return render_template("search.html", query=query, results=results)

#############################################
# Detail Route (for analysis and dashboard)
#############################################
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
    app.run(debug=True, threaded=True)
