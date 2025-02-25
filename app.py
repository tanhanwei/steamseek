from flask import Flask, render_template, request
import os
import json
import logging
from game_dashboard import build_steam_data_index, load_summaries, get_game_data_by_appid
from game_chatbot import semantic_search_query
from llm_processor import generate_game_analysis

app = Flask(__name__)

# Constants
STEAM_DATA_FILE = "data/steam_games_data.jsonl"
SUMMARIES_FILE = "data/summaries.jsonl"

# Preload the index and summaries
index_map = build_steam_data_index(STEAM_DATA_FILE)
summaries_dict = load_summaries(SUMMARIES_FILE)

def force_https(url: str) -> str:
    """
    If a URL starts with 'http://', convert to 'https://'.
    Useful to avoid mixed-content blocking in browsers.
    """
    if url.startswith("http://"):
        return "https://" + url[7:]
    return url

@app.route("/", methods=["GET", "POST"])
def search():
    query = ""
    results = []
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            raw_results = semantic_search_query(query, top_k=20)
            if raw_results:
                for r in raw_results:
                    appid = r.get("appid")
                    if not appid:
                        continue
                    game_data = get_game_data_by_appid(int(appid), STEAM_DATA_FILE, index_map)
                    if not game_data:
                        continue

                    # Compute review stats
                    reviews = game_data.get("reviews", [])
                    total_reviews = len(reviews)
                    positive_count = sum(1 for review in reviews if review.get("voted_up"))
                    pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

                    # Build media list for carousel
                    media = []

                    # 1) Header image
                    if game_data.get("header_image"):
                        media.append(force_https(game_data["header_image"]))

                    # 2) Screenshots
                    if isinstance(game_data.get("screenshots"), list):
                        for s in game_data["screenshots"]:
                            if isinstance(s, dict) and s.get("path_full"):
                                media.append(force_https(s["path_full"]))
                            else:
                                media.append(force_https(str(s)))

                    # 3) Videos from store_data
                    store_data = game_data.get("store_data", {})
                    if isinstance(store_data, dict):
                        movies = store_data.get("movies")
                        if isinstance(movies, list):
                            for movie in movies:
                                webm_480 = movie.get("webm", {}).get("480")
                                webm_max = movie.get("webm", {}).get("max")
                                mp4_480 = movie.get("mp4", {}).get("480")
                                mp4_max = movie.get("mp4", {}).get("max")

                                # Force HTTPS
                                if webm_480: webm_480 = force_https(webm_480)
                                if webm_max: webm_max = force_https(webm_max)
                                if mp4_480: mp4_480 = force_https(mp4_480)
                                if mp4_max: mp4_max = force_https(mp4_max)

                                # Prefer webm max -> mp4 max -> webm 480 -> mp4 480 -> fallback to thumbnail
                                if webm_max:
                                    media.append(webm_max)
                                elif mp4_max:
                                    media.append(mp4_max)
                                elif webm_480:
                                    media.append(webm_480)
                                elif mp4_480:
                                    media.append(mp4_480)
                                else:
                                    thumb = movie.get("thumbnail")
                                    if thumb:
                                        media.append(force_https(thumb))

                    # AI summary from cached summaries if available
                    summary_obj = summaries_dict.get(int(appid), {})
                    ai_summary = summary_obj.get("ai_summary", "")

                    results.append({
                        "appid": appid,
                        "name": game_data.get("name", "Unknown"),
                        "media": media,
                        "tags": [
                            g.get("description")
                            for g in game_data.get("genres", [])
                            if g.get("description")
                        ],
                        "pos_percent": pos_percent,
                        "total_reviews": total_reviews,
                        "ai_summary": ai_summary
                    })

    return render_template("search.html", query=query, results=results)


@app.route("/detail/<appid>")
def detail(appid):
    try:
        appid_int = int(appid)
    except ValueError:
        return "Invalid AppID", 400

    game_data = get_game_data_by_appid(appid_int, STEAM_DATA_FILE, index_map)
    if not game_data:
        return "Game not found", 404

    # If we don't have a full analysis in summaries, generate it now
    required_keys = {
        "ai_summary", "feature_sentiment", "standout_features",
        "community_feedback", "market_analysis", "feature_validation"
    }
    summary_obj = summaries_dict.get(appid_int)
    if not summary_obj or not required_keys.issubset(summary_obj.keys()):
        analysis = generate_game_analysis(game_data)
    else:
        analysis = summary_obj

    # Basic review stats
    reviews = game_data.get("reviews", [])
    total_reviews = len(reviews)
    positive_count = sum(1 for r in reviews if r.get("voted_up"))
    pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

    # Playtime distribution
    if "derived" in game_data and "playtime_distribution" in game_data["derived"]:
        playtime_distribution = game_data["derived"]["playtime_distribution"]
    else:
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
        playtime_distribution = [
            {"name": k, "value": v} for k, v in playtime_buckets.items()
        ]

    # Player growth data
    player_growth = game_data.get("player_growth", [])
    player_growth_available = bool(player_growth and isinstance(player_growth, list))

    # Build detail media carousel
    media = []
    # 1) header_image
    if game_data.get("header_image"):
        media.append(force_https(game_data["header_image"]))

    # 2) screenshots
    if isinstance(game_data.get("screenshots"), list):
        for s in game_data["screenshots"]:
            if isinstance(s, dict) and s.get("path_full"):
                media.append(force_https(s["path_full"]))
            else:
                media.append(force_https(str(s)))

    # 3) store_data -> movies
    store_data = game_data.get("store_data", {})
    if isinstance(store_data, dict):
        movies = store_data.get("movies")
        if isinstance(movies, list):
            for movie in movies:
                webm_480 = movie.get("webm", {}).get("480")
                webm_max = movie.get("webm", {}).get("max")
                mp4_480 = movie.get("mp4", {}).get("480")
                mp4_max = movie.get("mp4", {}).get("max")

                # Force https
                if webm_480: webm_480 = force_https(webm_480)
                if webm_max: webm_max = force_https(webm_max)
                if mp4_480: mp4_480 = force_https(mp4_480)
                if mp4_max: mp4_max = force_https(mp4_max)

                if webm_max:
                    media.append(webm_max)
                elif mp4_max:
                    media.append(mp4_max)
                elif webm_480:
                    media.append(webm_480)
                elif mp4_480:
                    media.append(mp4_480)
                else:
                    thumb = movie.get("thumbnail")
                    if thumb:
                        media.append(force_https(thumb))

    return render_template(
        "detail.html",
        game=game_data,
        analysis=analysis,
        pos_percent=pos_percent,
        total_reviews=total_reviews,
        playtime_distribution=playtime_distribution,
        player_growth=player_growth,
        player_growth_available=player_growth_available,
        media=media
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
