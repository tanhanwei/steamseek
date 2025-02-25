import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Get the OpenRouter API key from .env file
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in .env file.")

# OpenRouter API endpoint and model identifier
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct"


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
       • "market_position": string summarizing the game’s position in its market niche.
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
