import os
import json
import requests
from dotenv import load_dotenv
import logging # Add logging import if not already present
from typing import List, Dict, Any, Tuple, Optional # For type hinting

load_dotenv()

# Get the OpenRouter API key from .env file
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in .env file.")

# OpenRouter API endpoint and model identifier
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.0-flash-001"

# Configure logger for this module if needed, or rely on Flask's app.logger
logger = logging.getLogger(__name__)


def _prepare_llm_prompt(game_data: dict) -> str:
    """
    Prepare a prompt for the LLM that injects context from the raw Steam data.
    It uses the following fields: name, short_description, detailed_description, and top player reviews.
    """
    name = game_data.get("name", "Unknown Game")
    description = game_data.get("short_description", "")
    detailed_desc = game_data.get("detailed_description", "")
    reviews = game_data.get("reviews", [])
    
    # Get top 3 reviews (if available)
    top_reviews = reviews[:3]
    reviews_text = ""
    for i, review in enumerate(top_reviews, 1):
        review_text = review.get("review", "").strip()
        if review_text:
            reviews_text += f"\nReview {i}: {review_text}\n"
    
    # Build the prompt which instructs the LLM to output a JSON with the exact structure.
    prompt = f"""Using the following context from a Steam game, generate a complete JSON object with the exact structure below. Do not include any additional text.

The JSON object must have the following structure:

{{
  "ai_summary": "string",
  "feature_sentiment": [
    {{
      "feature": "string",
      "positive": integer,
      "negative": integer
    }}
    // ... more objects as needed
  ],
  "standout_features": ["string", "string", ...],
  "community_feedback": {{
    "strengths": ["string", "string", ...],
    "areas_for_improvement": ["string", "string", ...],
    "narrative": "string"
  }},
  "market_analysis": {{
    "market_position": "string",
    "competitive_advantage": "string",
    "underserved_audience": "string",
    "niche_rating": integer,
    "market_interest": integer,
    "narrative": "string"
  }},
  "feature_validation": {{
    "features_worth_implementing": ["string", "string", ...],
    "features_to_approach_with_caution": ["string", "string", ...],
    "narrative": "string"
  }}
}}

Detailed requirements:

1. "ai_summary":
   - Type: String.
   - Description: A comprehensive narrative summary (ideally around 400-500 words) covering the core gameplay mechanics, unique features, game style, pace, tone, multiplayer/singleplayer aspects, notable elements from reviews, and any creative or unusual elements.

2. "feature_sentiment":
   - Type: An array of objects.
   - Each object must have:
       • "feature": a string indicating the name of a key gameplay element (e.g., "Breeding", "Combat", "Customization", "Progression").
       • "positive": an integer (0–100) representing the positive sentiment score for that feature.
       • "negative": an integer (0–100) representing the negative sentiment score for that feature.

3. "standout_features":
   - Type: An array of strings.
   - Description: Each string is a brief phrase highlighting a unique selling point or innovative aspect of the game.

4. "community_feedback":
   - Type: Object with three keys:
       • "strengths": an array of strings listing the most frequently mentioned positive aspects from community reviews.
       • "areas_for_improvement": an array of strings listing common suggestions or weaknesses mentioned in reviews.
       • "narrative": a string providing a synthesized explanation of the overall community sentiment.

5. "market_analysis":
   - Type: Object with the following keys:
       • "market_position": string summarizing the game's position in its market niche.
       • "competitive_advantage": string describing what sets the game apart from its competitors.
       • "underserved_audience": string identifying a target demographic that is currently underserved.
       • "niche_rating": integer (0–100) rating how well the game fits a unique niche.
       • "market_interest": integer (0–100) indicating the overall market interest in the game.
       • "narrative": string providing an in-depth qualitative explanation tying together the quantitative ratings.

6. "feature_validation":
   - Type: Object with three keys:
       • "features_worth_implementing": an array of strings listing features that are performing well and should be emphasized.
       • "features_to_approach_with_caution": an array of strings listing features that received mixed or negative feedback and may need refinement.
       • "narrative": a string summarizing the overall recommendations regarding feature implementation.

IMPORTANT:
- Your output must be valid JSON with no additional text or formatting.
- Do not wrap the JSON in markdown or any explanation text—output only the JSON object.

Context:
Game: {name}

Official Description:
{description}

Detailed Description:
{detailed_desc}

Top Player Reviews:
{reviews_text}

Generate the JSON object now:"""
    return prompt


def generate_game_analysis(game_data: dict) -> dict:
    """
    Generate a complete game analysis by sending a prompt with context to the LLM
    via OpenRouter. Returns a JSON object with keys:
      - ai_summary
      - feature_sentiment
      - standout_features
      - community_feedback
      - market_analysis
      - feature_validation
    """
    prompt = _prepare_llm_prompt(game_data)
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://your-site.com",  # Optional; update with your site if needed.
        "X-Title": "Your Site Title"             # Optional; update accordingly.
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a skilled video game analyst who generates detailed, context-aware analyses of games. Your output must strictly follow the JSON structure provided."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            # Extract the content from the first choice
            content = result["choices"][0]["message"]["content"]
            # Attempt to parse the content as JSON
            analysis = json.loads(content)
            return analysis
        else:
            print(f"LLM API request failed with status {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        print(f"Exception during LLM request: {e}")
        return {}


def rerank_search_results(query: str, candidates: List[Dict[str, Any]], model: str = MODEL) -> Tuple[Optional[List[int]], Optional[str]]:
    """
    Uses an LLM via OpenRouter to re-rank search result candidates based on relevance to the query.

    Args:
        query: The user's search query.
        candidates: A list of dictionaries, where each dict has 'appid' (int) and 'ai_summary' (str).
        model: The identifier for the LLM model to use on OpenRouter.

    Returns:
        A tuple containing:
        - A list of appids (int) in the new relevance order, or None if an error occurs.
        - A string comment from the LLM explaining the ranking, or None if an error occurs or no comment is provided.
    """
    # DIRECT CONSOLE FEEDBACK - Add explicit print statements for immediate visibility 
    print("\n======= LLM RE-RANKING START =======")
    print(f"Query: '{query}'")
    print(f"Candidates: {len(candidates)} games")
    
    if not candidates:
        print("No candidates provided for re-ranking.")
        return [], "No candidates provided for re-ranking."

    # ---- Prepare the Prompt ----
    system_prompt = """You are a search relevance expert specializing in video games. Your task is to re-rank a list of games based on how relevant their summaries are to a user's query.

Analyze the user query and each game summary provided. Determine the best order for these games, from most relevant to least relevant, based *only* on the provided query and summaries.

Output ONLY a JSON object with the following exact structure:
{
  "ranked_appids": [appid1, appid2, ...],
  "ranking_comment": "A brief explanation of why you ranked the games this way."
}

- "ranked_appids": A list of integers representing the game AppIDs in the newly ranked order. Make sure to include ALL AppIDs from the input, with no duplicates.
- "ranking_comment": Your concise reasoning for the ranking decision.

IMPORTANT: AppIDs must be integers, not strings. No duplicate AppIDs are allowed.
Do not include any other text, preamble, or explanation outside the JSON structure."""

    # Construct the candidate part of the prompt separately for clarity
    candidate_texts = []
    original_appids = set()  # Keep track of original appids for validation
    
    for i, candidate in enumerate(candidates):
        # Ensure appid and summary are present and are of expected type
        appid = candidate.get('appid')
        summary = candidate.get('ai_summary', '')
        if appid is None:
            logger.warning(f"Skipping candidate with missing appid: {candidate}")
            continue
        original_appids.add(appid)
        candidate_texts.append(f"Game {i+1} (AppID: {appid}):\n{summary}\n---")
    
    joined_candidate_texts = '\n'.join(candidate_texts)

    user_prompt = f"""User Query: "{query}"

Games to re-rank:
{joined_candidate_texts}

Generate the JSON object containing the re-ranked AppIDs and your ranking comment based on relevance to the query. Remember that all AppIDs must be integers, not strings, and there should be no duplicates."""

    # ---- Make the API Call ----
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://your-site.com",  # Optional: Update with your actual site URL
        "X-Title": "SteamSeek ReRanker" # Optional: Update with your app title
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"} # Request JSON output if model supports it
    }

    print(f"Sending request to OpenRouter API with model: {model}")
    try:
        print("Making API call to OpenRouter...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(data), timeout=60) # Add timeout
        print(f"API response status code: {response.status_code}")
        
        # Check for non-200 status codes
        if response.status_code != 200:
            error_msg = f"OpenRouter API returned non-200 status: {response.status_code}"
            print(f"ERROR: {error_msg}")
            print(f"Response text: {response.text}")
            return None, error_msg
            
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        result = response.json()
        # Safely access nested keys
        try:
            content = result["choices"][0]["message"]["content"]
            print(f"Received response content from LLM")
        except (IndexError, KeyError, TypeError) as e:
            error_msg = f"Could not extract content from LLM response structure: {e}."
            print(f"ERROR: {error_msg}")
            print(f"Response structure: {result}")
            return None, error_msg

        # Parse the JSON response
        try:
            print("Parsing LLM response as JSON...")
            analysis = json.loads(content)
            print(f"Parsed response: {json.dumps(analysis, indent=2)}")
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM JSON response: {e}"
            print(f"ERROR: {error_msg}")
            print(f"Raw content that couldn't be parsed: {content}")
            return None, error_msg

        # Get the ranked appids
        ranked_appids = analysis.get("ranked_appids", [])
        comment = analysis.get("ranking_comment", "No comment provided by LLM.")

        # Basic validation and type conversion
        try:
            # Convert any string appids to integers
            processed_ranked_appids = []
            for appid in ranked_appids:
                if isinstance(appid, str):
                    processed_ranked_appids.append(int(appid))
                elif isinstance(appid, int):
                    processed_ranked_appids.append(appid)
                else:
                    print(f"WARNING: Skipping non-integer/non-string appid: {appid}")
                    
            # Remove duplicates while preserving order
            seen = set()
            unique_ranked_appids = []
            for appid in processed_ranked_appids:
                if appid not in seen:
                    seen.add(appid)
                    unique_ranked_appids.append(appid)
                else:
                    print(f"WARNING: Removed duplicate appid: {appid}")
                    
            ranked_appids = unique_ranked_appids
            
            if not ranked_appids:
                error_msg = "After processing, no valid AppIDs remain."
                print(f"ERROR: {error_msg}")
                return None, error_msg
        except ValueError as e:
            error_msg = f"Error converting string appids to integers: {e}"
            print(f"ERROR: {error_msg}")
            print(f"Raw ranked_appids: {ranked_appids}")
            return None, error_msg

        # Check if all original appids are present
        if not original_appids.issubset(set(ranked_appids)):
            print(f"WARNING: LLM re-ranking did not return all original AppIDs.")
            print(f"Expected: {original_appids}")
            print(f"Received: {set(ranked_appids)}")
            
            # Add missing appids to the end of the list
            missing_appids = original_appids - set(ranked_appids)
            if missing_appids:
                print(f"Adding {len(missing_appids)} missing AppIDs to the end of the ranked list.")
                ranked_appids.extend(missing_appids)
                
            # Remove any extra appids that weren't in the original list
            extra_appids = set(ranked_appids) - original_appids
            if extra_appids:
                ranked_appids = [appid for appid in ranked_appids if appid not in extra_appids]
                print(f"Removed {len(extra_appids)} extra AppIDs that weren't in the original candidates.")

        print(f"Re-ranking successful! Comment from LLM: {comment}")
        print(f"New order: {ranked_appids}")
        print("======= LLM RE-RANKING END =======\n")
        
        return ranked_appids, comment

    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to LLM API: {e}"
        print(f"ERROR: {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error during LLM re-ranking: {e}"
        print(f"ERROR: {error_msg}")
        import traceback
        print(traceback.format_exc())
        return None, error_msg


def optimize_search_query(original_query: str, model: str = MODEL) -> Tuple[str, str]:
    """
    Uses the LLM to transform a user's natural language query into optimized keywords 
    for semantic search.
    
    Args:
        original_query: The user's original search query
        model: The identifier for the LLM model to use on OpenRouter
        
    Returns:
        A tuple containing:
        - Optimized search keywords (str)
        - Explanation of the transformation (str)
    """
    print(f"\n------ OPTIMIZING SEARCH QUERY ------")
    print(f"Original query: '{original_query}'")
    
    # Prepare the prompt
    system_prompt = """You are a search optimization expert for a video game search engine. 
Your task is to transform user queries into the most effective search keywords.

Users often express what they want in natural language, but vector search works better with clear, concise keywords.
Transform the user's query into the most effective search terms that will find relevant games.

Return ONLY a JSON object with this exact structure:
{
  "optimized_keywords": "the optimized search keywords",
  "explanation": "brief explanation of your transformation"
}

The optimized_keywords should be concise (2-5 words is ideal) and focus on the key gaming concepts.
The explanation should briefly explain your thought process in transforming the query.
"""

    user_prompt = f"""Transform this user query into effective search keywords:
"{original_query}"

Return only the JSON with optimized search keywords and a brief explanation.
"""

    # Make the API call
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://your-site.com",
        "X-Title": "SteamSeek Query Optimizer"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    print("Calling LLM to optimize search keywords...")
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(data), timeout=15)
        
        if response.status_code != 200:
            print(f"ERROR: OpenRouter API returned status {response.status_code}")
            return original_query, "Error: Could not optimize query"
            
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse the response
        analysis = json.loads(content)
        optimized_keywords = analysis.get("optimized_keywords", original_query)
        explanation = analysis.get("explanation", "No explanation provided")
        
        print(f"Optimized keywords: '{optimized_keywords}'")
        print(f"Explanation: {explanation}")
        print("------ OPTIMIZATION COMPLETE ------\n")
        
        return optimized_keywords, explanation
        
    except Exception as e:
        print(f"ERROR during query optimization: {e}")
        # Fall back to original query if optimization fails
        return original_query, f"Error: {str(e)}"


# When called externally (e.g., from game_dashboard.py), call generate_game_analysis(game_data)
# and return the complete JSON analysis.
# When run directly, this script loads "steam_data_sample.txt" and tests the LLM processing.
if __name__ == "__main__":
    import sys

    sample_file = "steam_data_sample.txt"
    if not os.path.exists(sample_file):
        print(f"Sample file {sample_file} not found.")
        sys.exit(1)

    try:
        with open(sample_file, "r", encoding="utf-8") as f:
            # Assuming the file contains one JSON per line; load the first one.
            line = f.readline()
            if not line:
                print("No data found in sample file.")
                sys.exit(1)
            game_data = json.loads(line)
    except Exception as e:
        print(f"Error reading sample file: {e}")
        sys.exit(1)

    # Generate analysis via the LLM
    analysis = generate_game_analysis(game_data)
    # Pretty-print the resulting JSON analysis
    print(json.dumps(analysis, indent=2))

    # --- Test Re-ranking ---
    print("\n--- Testing Re-ranking ---")
    test_query = "Games with crafting and survival elements"
    test_candidates = [
        {"appid": 101, "ai_summary": "A survival game where you gather resources, build shelters, and fight monsters. Crafting is essential."},
        {"appid": 202, "ai_summary": "A relaxing puzzle game involving matching colors. No survival or crafting."},
        {"appid": 303, "ai_summary": "Explore a vast open world, craft tools and gear, and survive against the elements and wildlife."},
        {"appid": 404, "ai_summary": "A narrative adventure game focusing on story and characters."}
    ]
    ranked_ids, comment = rerank_search_results(test_query, test_candidates)
    if ranked_ids is not None:
        print("Re-ranked AppIDs:", ranked_ids)
        print("LLM Comment:", comment)
    else:
        print("Re-ranking failed.")
        print("Failure Reason:", comment) # Comment might contain error message
