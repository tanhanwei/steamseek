import streamlit as st
import json
import os
import logging
from typing import Dict, Any, Optional

# Import your Pinecone-based search helper from game_chatbot.py
from game_chatbot import semantic_search_query

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


###############################################################################
# 1) GLOBAL CONSTANTS - FILE PATHS
###############################################################################
STEAM_DATA_FILE = "data/steam_games_data.jsonl"   # Large 4GB file with raw Steam data
SUMMARIES_FILE = "data/summaries.jsonl"           # Smaller file with appid->ai_summary


###############################################################################
# 2) CACHED LOAD FUNCTIONS
###############################################################################
@st.cache_data(show_spinner=False)
def build_steam_data_index(file_path: str) -> Dict[int, int]:
    """
    Builds an index mapping:
        appid (int) -> file offset (int)
    for the huge JSONL file so we can do random-access for a given appid.
    Displays a progress bar while building.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {}

    # Count lines to track progress
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
                    appid_int = int(appid)
                    index_map[appid_int] = offset
            except Exception as e:
                logging.warning(f"Line {i} parse error: {e}")

            offset = f.tell()

            # Update progress bar occasionally
            if (i+1) % 5000 == 0 or (i+1) == total_lines:
                progress_bar.progress((i+1) / total_lines)

    logging.info(f"Index building complete. Mapped {len(index_map)} appids.")
    return index_map


@st.cache_data(show_spinner=False)
def load_summaries(file_path: str) -> Dict[int, Dict[str, Any]]:
    """
    Loads 'summaries.jsonl' fully into memory, returning a dict keyed by appid.
    Each line is expected to be a JSON object with at least:
      { "appid": <int>, "name": <str>, "short_description": <str>, "ai_summary": <str> }
    """
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
    """
    Using the index_map, do a random seek in steam_games_data.jsonl
    for the line corresponding to the given appid.
    Returns the parsed JSON dict or None if not found.
    """
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
            data = json.loads(line)
            return data
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

        # 1. Pinecone semantic search
        results = semantic_search_query(query, top_k=20)
        if not results:
            st.write("No matches found.")
            return

        # 2. Display each result. For each appid, fetch partial raw data for the image
        for r in results:
            appid = r.get("appid")
            if appid is None:
                continue

            name = r.get("name", "Unknown")
            score = round(r.get("similarity_score", 0.0), 3)

            # Try to fetch some raw data from big file
            game_data = get_game_data_by_appid(int(appid), STEAM_DATA_FILE, index_map)

            # Layout
            col1, col2 = st.columns([1,4])
            with col1:
                # Attempt to display an image
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
# 4) DETAIL PAGE
###############################################################################
def show_detail_page(appid_str: str,
                     index_map: Dict[int, int],
                     summaries_dict: Dict[int, Dict[str, Any]]):
    """Display a detailed page for a given AppID."""

    # Convert to int
    try:
        appid = int(appid_str)
    except ValueError:
        st.error("Invalid AppID.")
        return

    # Load raw game data
    game_data = get_game_data_by_appid(appid, STEAM_DATA_FILE, index_map)
    if not game_data:
        st.error("Game not found in local data!")
        return

    # Title
    title = game_data.get("title", game_data.get("name", "Unknown Game"))
    st.title(title)

    # Extra info from raw data
    release_date = game_data.get("release_date", "Unknown Date")
    developer = game_data.get("developer", "Unknown Dev")
    publisher = game_data.get("publisher", "Unknown Publisher")

    st.write(f"**AppID**: {appid}")
    st.write(f"**Developer**: {developer}")
    st.write(f"**Publisher**: {publisher}")
    st.write(f"**Release Date**: {release_date}")

    # Market presence: languages, platforms
    languages = game_data.get("supported_languages", [])
    if isinstance(languages, list) and languages:
        st.write("**Supported Languages**:", ", ".join(languages))
    elif isinstance(languages, str):
        st.write("**Supported Languages**:", languages)

    platforms = game_data.get("platforms", {})
    if platforms:
        # platforms might be {"windows":true,"mac":false,"linux":true} etc.
        # let's turn it into a string
        supported = [p for p, val in platforms.items() if val]
        st.write("**Platforms**:", ", ".join(supported) if supported else "None")

    # Categories & Features
    categories = game_data.get("categories", [])
    if categories:
        st.write("**Categories**:", ", ".join(categories))

    # Show screenshots as a "carousel" via a slider
    screenshots = game_data.get("screenshots", [])
    if screenshots:
        st.subheader("Screenshots")
        # We'll let the user pick an index to display
        idx = st.slider("Select screenshot", 0, len(screenshots)-1, 0, key="screenshot_slider")
        st.image(screenshots[idx], use_container_width=True)

    # Show videos similarly
    videos = game_data.get("videos", [])
    if videos:
        st.subheader("Videos")
        vid_idx = st.slider("Select video", 0, len(videos)-1, 0, key="video_slider")
        st.video(videos[vid_idx])

    # If there's a header image
    header_img = game_data.get("header_image")
    if header_img:
        st.subheader("Header Image")
        st.image(header_img, use_container_width=True)

    # Show top reviews if present
    reviews = game_data.get("reviews", [])
    if reviews:
        st.subheader("Some Top Reviews")
        # Show first 3
        for r in reviews[:3]:
            rating = r.get("rating", "No rating")
            review_txt = r.get("review", "")
            st.write(f"- **Rating**: {rating}, **Review**: {review_txt}")

    # Show AI summary from summaries.jsonl
    st.subheader("AI Summary")
    summary_obj = summaries_dict.get(appid)
    if summary_obj:
        ai_summary = summary_obj.get("ai_summary", "No AI summary found.")
        st.write(ai_summary)
    else:
        st.write("No summary found in summaries.jsonl")


###############################################################################
# 5) MAIN
###############################################################################
def main():
    st.set_page_config(page_title="Game Dashboard", layout="wide")

    # Build or retrieve the index (cached)
    index_map = build_steam_data_index(STEAM_DATA_FILE)
    if not index_map:
        st.error("Could not build index map. Check logs for errors.")
        return

    # Load summaries (cached)
    summaries_dict = load_summaries(SUMMARIES_FILE)

    # Use st.query_params (non-deprecated) to route between pages
    params = st.query_params
    page = params.get("page", "search")
    appid_str = params.get("appid", None)

    if page == "detail" and appid_str:
        show_detail_page(appid_str, index_map, summaries_dict)
    else:
        show_search_page(index_map, summaries_dict)


if __name__ == "__main__":
    main()
