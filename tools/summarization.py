import json
import time
import requests
from typing import Optional, Dict, Any
from config import *

class GameSummarizer:
    def __init__(self):
        self.api_url = OPENROUTER_API_URL
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL

    def create_summary_prompt(self, game_data: Dict[str, Any]) -> str:
        """
        Creates a structured prompt for game summarization.
        """
        description = game_data.get('detailed_description') or \
                     game_data.get('short_description', '')
        
        reviews = game_data.get('reviews', [])
        review_texts = [r.get('review', '') for r in reviews[:3]]
        review_block = "\n\n".join(review_texts)

        return f"""Analyze this game and provide a structured summary:

Game: {game_data.get('name', 'Unknown Game')}

Description:
{description}

Top Reviews:
{review_block}

Create a concise summary (400-500 words) that covers:
1. Core gameplay mechanics and systems
2. Unique features or innovations
3. Game style, pace, and overall tone
4. Multiplayer/singleplayer aspects
5. Notable elements mentioned in reviews
6. Any unusual or creative weapon/item usage

Focus on specific gameplay elements rather than marketing language.
Summary:"""

    def call_openrouter(self, 
                       prompt: str, 
                       max_tokens: int = 800, 
                       temperature: float = 0.7) -> Optional[str]:
        """
        Calls OpenRouter API with error handling and retries.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and data["choices"]:
                    return data["choices"][0].get("message", {}).get("content", "").strip()
                
                return None

            except requests.exceptions.RequestException as e:
                print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue

        return None

    def summarize_game(self, game_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates a summary for a single game.
        """
        prompt = self.create_summary_prompt(game_data)
        return self.call_openrouter(prompt)