import streamlit as st
import json
import os
import logging
import pandas as pd
import plotly.express as px
from typing import Dict, Any, Optional

# Import your semantic search helper
from game_chatbot import semantic_search_query

# Import the LLM processor
from llm_processor import generate_game_analysis

###############################################################################
# 1) GLOBAL CONSTANTS - FILE PATHS
###############################################################################
STEAM_DATA_FILE = "data/steam_games_data.jsonl"   # Large 4GB file with raw Steam data
SUMMARIES_FILE = "data/summaries.jsonl"           # File with appid->ai_summary (cache)

###############################################################################
# 2) CACHED LOAD FUNCTIONS
###############################################################################
@st.cache_data(show_spinner=False)
def build_steam_data_index(file_path: str) -> Dict[int, int]:
    """Builds an index map of appid -> file offset in the big JSONL file."""
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {}

    st.info("Reading total lines... Please wait.")
    with open(file_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
    logging.info(f"Total lines in {file_path}: {total_lines}")

    st.info("Building index for steam games data...")
    progress_bar = st.progress(0)
    index_map = {}
    with open(file_path, "r", encoding="utf-8") as f:
        offset = 0
        for i in range(total_lines):
            line = f.readline()
            if not line:
                break
            try:
                data = json.loads(line)
                appid = data.get("appid", None)
                if appid is not None:
                    index_map[int(appid)] = offset
            except Exception as e:
                logging.warning(f"Line {i} parse error: {e}")
            offset = f.tell()
            if (i+1) % 5000 == 0 or (i+1) == total_lines:
                progress_bar.progress((i+1) / total_lines)
    logging.info(f"Index building complete. Mapped {len(index_map)} appids.")
    return index_map

@st.cache_data(show_spinner=False)
def load_summaries(file_path: str) -> Dict[int, Dict[str, Any]]:
    """Loads the smaller AI summaries file (summaries.jsonl) fully into memory."""
    if not os.path.exists(file_path):
        logging.warning(f"Summaries file not found: {file_path}")
        return {}
    summaries_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                appid = obj.get("appid")
                if appid is not None:
                    summaries_dict[int(appid)] = obj
            except Exception as e:
                logging.warning(f"Error parsing summaries line: {e}")
    logging.info(f"Loaded {len(summaries_dict)} summaries from {file_path}")
    return summaries_dict

def get_game_data_by_appid(appid: int, file_path: str, index_map: Dict[int, int]) -> Optional[Dict]:
    """Random-access lookup of the game data from the big JSONL file using the prebuilt index."""
    offset = index_map.get(appid)
    if offset is None:
        logging.info(f"AppID {appid} not found in index map.")
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        f.seek(offset)
        line = f.readline()
        if not line:
            return None
        try:
            return json.loads(line)
        except Exception as e:
            logging.error(f"Failed to parse line at offset={offset}: {e}")
            return None

###############################################################################
# 3) SEARCH PAGE
###############################################################################
def show_search_page(index_map: Dict[int, int], summaries_dict: Dict[int, Dict[str, Any]]):
    st.title("Game Design Dashboard")
    st.subheader("Search by Features, Mechanics, or Keywords")

    query = st.text_input("Enter search keywords here:")
    if query:
        st.write(f"**Search Results** for '{query}':")
        results = semantic_search_query(query, top_k=20)
        if not results:
            st.write("No matches found.")
            return

        for r in results:
            appid = r.get("appid")
            if appid is None:
                continue

            name = r.get("name", "Unknown")
            score = round(r.get("similarity_score", 0.0), 3)
            game_data = get_game_data_by_appid(int(appid), STEAM_DATA_FILE, index_map)

            col1, col2 = st.columns([1, 4])
            with col1:
                if game_data:
                    header_img = game_data.get("header_image")
                    if header_img:
                        st.image(header_img, use_container_width=True)
                    else:
                        screenshots = game_data.get("screenshots", [])
                        if len(screenshots) > 0:
                            st.image(screenshots[0], use_container_width=True)
                        else:
                            st.write("No image found.")
                else:
                    st.write("No image found.")

            with col2:
                st.markdown(f"### {name}")
                st.write(f"AppID: {appid}")
                st.write(f"Similarity: {score}")

                # Link to detail page -> new tab
                detail_url = f"?page=detail&appid={appid}"
                link_html = f'<a href="{detail_url}" target="_blank" style="color:blue;font-weight:bold;">Analyze</a>'
                st.markdown(link_html, unsafe_allow_html=True)

            st.write("---")
    else:
        st.write("Type something in the box above to begin searching.")

###############################################################################
# 4) DETAIL PAGE WITH LLM PROCESSING
###############################################################################
def show_detail_page(appid_str: str,
                     index_map: Dict[int, int],
                     summaries_dict: Dict[int, Dict[str, Any]]):
    """Displays the detailed analysis page for a single game, with LLM-based analysis."""
    try:
        appid = int(appid_str)
    except ValueError:
        st.error("Invalid AppID.")
        return

    # 1. Load raw game data
    game_data = get_game_data_by_appid(appid, STEAM_DATA_FILE, index_map)
    if not game_data:
        st.error("Game not found in local data!")
        return

    # 2. Possibly call the LLM if we don't have a complete cached summary
    required_keys = {
        "ai_summary", "feature_sentiment", "standout_features",
        "community_feedback", "market_analysis", "feature_validation"
    }
    summary_obj = summaries_dict.get(appid)
    if not summary_obj or not required_keys.issubset(summary_obj.keys()):
        st.info("Generating full analysis via LLM... (this may take a moment)")
        analysis = generate_game_analysis(game_data)
        # Optionally, write the new analysis back to your summaries file
    else:
        analysis = summary_obj

    # 3. Extract LLM-generated fields
    ai_summary = analysis.get("ai_summary", "No AI summary available.")
    feature_sentiment = analysis.get("feature_sentiment", [])
    standout_features = analysis.get("standout_features", [])
    community_feedback = analysis.get("community_feedback", {
        "strengths": [], "areas_for_improvement": [], "narrative": ""
    })
    market_analysis = analysis.get("market_analysis", {
        "market_position": "", "competitive_advantage": "",
        "underserved_audience": "", "niche_rating": 0,
        "market_interest": 0, "narrative": ""
    })
    feature_validation = analysis.get("feature_validation", {
        "features_worth_implementing": [],
        "features_to_approach_with_caution": [],
        "narrative": ""
    })

    # 4. Compute basic metrics from raw reviews
    reviews = game_data.get("reviews", [])
    total_reviews = len(reviews)
    positive_count = sum(1 for r in reviews if r.get("voted_up"))
    pos_percent = (positive_count / total_reviews * 100) if total_reviews > 0 else 0

    # 5. Build a playtime distribution from the raw reviews
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

    # 6. Basic sentiment breakdown
    sentiment_breakdown = [
        {"name": "Positive", "value": positive_count},
        {"name": "Negative", "value": total_reviews - positive_count}
    ]

    # 7. Recent reviews
    recent_reviews = reviews[:3]

    # 8. Player growth: load from raw data if available; else fallback
    player_growth = game_data.get("player_growth")
    if not player_growth or not isinstance(player_growth, list):
        player_growth = [
            {"month": "Jan", "players": 125},
            {"month": "Feb", "players": 350},
            {"month": "Mar", "players": 410},
            {"month": "Apr", "players": 380},
            {"month": "May", "players": 425},
        ]

    # 9. Basic store data checks
    is_free = False
    if "store_data" in game_data and isinstance(game_data["store_data"], dict):
        is_free = game_data["store_data"].get("is_free", False)
    developers = game_data.get("developers") or [game_data.get("developer", "Unknown Dev")]
    release_date = game_data.get("release_date", "Unknown Date")
    publishers = game_data.get("publishers") or [game_data.get("publisher", "Unknown Publisher")]

    # 10. Similar games: if present in store_data, else fallback
    similar_games = []
    if "store_data" in game_data and isinstance(game_data["store_data"], dict):
        maybe_similar = game_data["store_data"].get("similar_games")
        if maybe_similar and isinstance(maybe_similar, list):
            similar_games = maybe_similar

    if not similar_games:
        similar_games = ["Game A", "Game B", "Game C", "Game D"]  # fallback

    # Inject Custom CSS with improved card styling
    st.markdown("""
    <style>
    body, .block-container {
        background-color: #f8f9fc !important;
        font-family: "Open Sans", sans-serif;
    }
    header, footer {visibility: hidden;}

    .top-bar {
        background-color: #4F46E5;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .top-bar-left h1 {
        margin: 0;
        font-size: 1.8rem;
    }
    .top-bar-left p {
        margin: 0;
        font-size: 0.9rem;
        color: #e2e2ff;
    }
    .top-bar-right {
        display: flex;
        gap: 1.5rem;
    }
    .metric-box {
        background-color: rgba(255,255,255,0.2);
        padding: 0.6rem 1rem;
        border-radius: 0.4rem;
        text-align: center;
    }
    .metric-box h2 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: bold;
    }
    .metric-box p {
        margin: 0;
        font-size: 0.8rem;
    }
    /* We remove the direct <div> injection approach
       in favor of with st.container() for each card. */

    .card-header {
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    .card-subheader {
        font-size: 1rem;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }

    /* The container approach for each card can still use .card styling */
    .card {
        background-color: #ffffff;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 100%;
    }
    .element-container .element-container svg {
        background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- TOP BAR ------------
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-left">
            <h1>{game_data.get("name", "Unknown Game")}</h1>
            <p>{", ".join(developers)} • {release_date} • {"Free to Play" if is_free else "Paid"}</p>
        </div>
        <div class="top-bar-right">
            <div class="metric-box">
                <h2>{pos_percent:.0f}%</h2>
                <p>Positive</p>
            </div>
            <div class="metric-box">
                <h2>{total_reviews}</h2>
                <p>Reviews</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- TABS ------------
    tab_overview, tab_features, tab_community, tab_market = st.tabs([
        "Overview", "Features & Mechanics", "Community & Reviews", "Market Analysis"
    ])

    # ========== TAB 1: OVERVIEW ==========
    with tab_overview:
        col1, col2 = st.columns([2, 1])

        # --- Left Column: Game Summary ---
        with col1:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Game Summary</div>', unsafe_allow_html=True)

                short_desc = game_data.get("short_description", "No short description available.")
                st.write(short_desc)

                st.write("**AI Analysis:**", ai_summary)

                if "store_data" in game_data and isinstance(game_data["store_data"], dict):
                    genres = game_data["store_data"].get("genres", [])
                    if isinstance(genres, list) and genres:
                        joined_genres = ", ".join([g["description"] for g in genres if "description" in g])
                        st.markdown(f"**Genres:** {joined_genres}")

                st.markdown('</div>', unsafe_allow_html=True)

        # --- Right Column: Key Metrics ---
        with col2:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Key Metrics</div>', unsafe_allow_html=True)

                avg_play = (sum(r.get("playtime_forever", 0) for r in reviews) / len(reviews) / 60) if reviews else 0
                st.markdown(f"**Player Engagement:** {avg_play:.1f}h avg playtime")
                st.progress(avg_play / 100)

                mi = market_analysis.get('market_interest', 0)
                st.markdown(f"**Market Interest:** {mi}%")
                st.progress(mi / 100)

                nr = market_analysis.get('niche_rating', 0)
                st.markdown(f"**Niche Rating:** {nr}%")
                st.progress(nr / 100)

                st.markdown('</div>', unsafe_allow_html=True)

        # Another row: left for recent reviews, right for playtime distribution
        col3, col4 = st.columns([2, 1])

        with col3:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Recent Reviews</div>', unsafe_allow_html=True)

                if recent_reviews:
                    for review in recent_reviews:
                        vote_status = "Positive" if review.get("voted_up") else "Negative"
                        playtime_hours = review.get("playtime_forever", 0) / 60
                        review_text = review.get('review', '')
                        st.markdown(f"**[{vote_status}]** {review_text}")
                        st.caption(f"Playtime: {playtime_hours:.1f}h")
                else:
                    st.write("No reviews available.")

                st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Playtime Distribution</div>', unsafe_allow_html=True)

                try:
                    df_play = pd.DataFrame(playtime_distribution)
                    fig_play = px.pie(df_play, names="name", values="value", hole=0.3)
                    fig_play.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                    st.plotly_chart(fig_play, use_container_width=True)
                except Exception as e:
                    st.write("Error generating chart:", e)

                st.markdown('</div>', unsafe_allow_html=True)

        # Player Growth Trend
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-header">Player Growth Trend</div>', unsafe_allow_html=True)

            try:
                df_trend = pd.DataFrame(player_growth)
                if not df_trend.empty and "month" in df_trend.columns and "players" in df_trend.columns:
                    fig_trend = px.line(df_trend, x="month", y="players", markers=True)
                    fig_trend.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.write("No valid player growth data available.")
            except Exception as e:
                st.write("Error generating trend chart:", e)

            st.markdown('</div>', unsafe_allow_html=True)

    # ========== TAB 2: FEATURES & MECHANICS ==========
    with tab_features:
        col1, col2 = st.columns([1, 1])

        # Feature Sentiment
        with col1:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Feature Sentiment</div>', unsafe_allow_html=True)

                if feature_sentiment:
                    df_feat = pd.DataFrame(feature_sentiment)
                    if not df_feat.empty and "feature" in df_feat.columns:
                        fig_feat = px.bar(
                            df_feat,
                            y="feature",
                            x=["positive", "negative"],
                            orientation="h",
                            barmode="stack",
                            labels={"value": "Sentiment (%)", "feature": "Feature"},
                            color_discrete_map={"positive": "#4caf50", "negative": "#f44336"}
                        )
                        fig_feat.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                        st.plotly_chart(fig_feat, use_container_width=True)
                    else:
                        st.write("No valid feature sentiment data available.")
                else:
                    st.write("No feature sentiment data available.")

                st.markdown('</div>', unsafe_allow_html=True)

        # Standout Features
        with col2:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Standout Features</div>', unsafe_allow_html=True)

                if standout_features:
                    for feature in standout_features:
                        st.markdown(f"- **{feature}**")
                else:
                    st.write("No standout features available.")

                st.markdown('</div>', unsafe_allow_html=True)

        # Similar Games
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-header">Similar Games</div>', unsafe_allow_html=True)

            cols = st.columns(len(similar_games))
            for idx, game in enumerate(similar_games):
                with cols[idx]:
                    st.markdown(f"**{game}**")
                    st.caption("Short descriptor here")

            st.markdown('</div>', unsafe_allow_html=True)

    # ========== TAB 3: COMMUNITY & REVIEWS ==========
    with tab_community:
        col1, col2 = st.columns([1, 1])

        # Review Sentiment
        with col1:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Review Sentiment</div>', unsafe_allow_html=True)

                try:
                    df_sent = pd.DataFrame(sentiment_breakdown)
                    fig_sent = px.pie(df_sent, names="name", values="value", hole=0.4)
                    fig_sent.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                    st.plotly_chart(fig_sent, use_container_width=True)
                    st.markdown(f"**{sentiment_breakdown[0]['value']}** Positive, **{sentiment_breakdown[1]['value']}** Negative")
                except Exception as e:
                    st.write("Error generating sentiment chart:", e)

                st.markdown('</div>', unsafe_allow_html=True)

        # Top Community Feedback
        with col2:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Top Community Feedback</div>', unsafe_allow_html=True)

                st.markdown("**Strengths:**")
                if community_feedback.get("strengths"):
                    for item in community_feedback["strengths"]:
                        st.write(f"- {item}")
                else:
                    st.write("No strengths available.")

                st.markdown("**Areas for Improvement:**")
                if community_feedback.get("areas_for_improvement"):
                    for item in community_feedback["areas_for_improvement"]:
                        st.write(f"- {item}")
                else:
                    st.write("No areas for improvement available.")

                if community_feedback.get("narrative"):
                    st.markdown("**Overall Community Narrative:**")
                    st.write(community_feedback["narrative"])

                st.markdown('</div>', unsafe_allow_html=True)

            # Community Engagement
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Community Engagement</div>', unsafe_allow_html=True)

                colA, colB, colC, colD = st.columns(4)
                with colA:
                    st.metric("Reviews", value=total_reviews)
                with colB:
                    st.metric("Active Players", value="N/A")
                with colC:
                    st.metric("Positive Reviews", f"{pos_percent:.0f}%")
                with colD:
                    avg_play = (sum(r.get("playtime_forever", 0) for r in reviews) / len(reviews) / 60) if reviews else 0
                    st.metric("Avg. Playtime", f"{avg_play:.1f}h")

                st.markdown('</div>', unsafe_allow_html=True)

    # ========== TAB 4: MARKET ANALYSIS & FEATURE VALIDATION ==========
    with tab_market:
        col1, col2 = st.columns([1, 1])

        # Market Analysis
        with col1:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Market Position</div>', unsafe_allow_html=True)

                st.write(market_analysis.get("market_position", "N/A"))
                st.markdown(f"**Underserved Audience:** {market_analysis.get('underserved_audience', 'N/A')}")

                st.markdown("### Competitive Advantage")
                st.write(market_analysis.get("competitive_advantage", "N/A"))

                st.markdown("**Narrative:**")
                st.write(market_analysis.get("narrative", ""))

                st.markdown('</div>', unsafe_allow_html=True)

        # Feature Validation
        with col2:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">Feature Validation Summary</div>', unsafe_allow_html=True)

                st.markdown("**Features Worth Implementing:**")
                if feature_validation.get("features_worth_implementing"):
                    for feat in feature_validation["features_worth_implementing"]:
                        st.write(f"- {feat}")
                else:
                    st.write("No data available.")

                st.markdown("**Features to Approach with Caution:**")
                if feature_validation.get("features_to_approach_with_caution"):
                    for feat in feature_validation["features_to_approach_with_caution"]:
                        st.write(f"- {feat}")
                else:
                    st.write("No data available.")

                if feature_validation.get("narrative"):
                    st.markdown("**Narrative:**")
                    st.write(feature_validation["narrative"])

                st.markdown('</div>', unsafe_allow_html=True)


###############################################################################
# 5) MAIN
###############################################################################
def main():
    st.set_page_config(page_title="Game Dashboard", layout="wide")

    index_map = build_steam_data_index(STEAM_DATA_FILE)
    if not index_map:
        st.error("Could not build index map. Check logs for errors.")
        return

    summaries_dict = load_summaries(SUMMARIES_FILE)

    params = st.query_params
    page = params.get("page", "search")
    appid_str = params.get("appid", None)

    if page == "detail" and appid_str:
        show_detail_page(appid_str, index_map, summaries_dict)
    else:
        show_search_page(index_map, summaries_dict)

if __name__ == "__main__":
    main()
