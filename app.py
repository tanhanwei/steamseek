from flask import Flask, render_template, request, redirect, url_for
import os, json, logging
import pandas as pd
import plotly.express as px
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

@app.route("/", methods=["GET", "POST"])
def search():
    query = ""
    results = []
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            raw_results = semantic_search_query(query, top_k=20)
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
                # Get preview image
                preview_image = game_data.get("header_image") or (game_data.get("screenshots", [None])[0])
                # Get tags from genres
                tags = [g.get("description") for g in game_data.get("genres", []) if g.get("description")]
                results.append({
                    "appid": appid,
                    "name": game_data.get("name", "Unknown"),
                    "preview_image": preview_image,
                    "tags": tags,
                    "pos_percent": pos_percent,
                    "total_reviews": total_reviews
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

    # Use cached summary if available; otherwise call LLM processing.
    required_keys = {"ai_summary", "feature_sentiment", "standout_features",
                     "community_feedback", "market_analysis", "feature_validation"}
    summary_obj = summaries_dict.get(appid_int)
    if not summary_obj or not required_keys.issubset(summary_obj.keys()):
        analysis = generate_game_analysis(game_data)
        # Optionally, update summaries_dict or write back to file.
    else:
        analysis = summary_obj

    # Compute review metrics
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

    # Player growth (from data if available, else fallback)
    player_growth = game_data.get("player_growth")
    if not player_growth or not isinstance(player_growth, list):
        player_growth = [
            {"month": "Jan", "players": 125},
            {"month": "Feb", "players": 350},
            {"month": "Mar", "players": 410},
            {"month": "Apr", "players": 380},
            {"month": "May", "players": 425},
        ]

    # Similar games from store_data if present; else fallback
    similar_games = []
    if "store_data" in game_data and isinstance(game_data["store_data"], dict):
        maybe_similar = game_data["store_data"].get("similar_games")
        if maybe_similar and isinstance(maybe_similar, list):
            similar_games = maybe_similar
    if not similar_games:
        similar_games = ["Game A", "Game B", "Game C", "Game D"]

    return render_template("detail.html",
                           game=game_data,
                           analysis=analysis,
                           pos_percent=pos_percent,
                           total_reviews=total_reviews,
                           playtime_distribution=playtime_distribution,
                           player_growth=player_growth,
                           similar_games=similar_games)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
