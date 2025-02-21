import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
MODE = os.getenv("MODE", "api").lower()
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

# File paths
DATA_DIR = "data"
GAMES_FILE = os.path.join(DATA_DIR, "steam_games_data.jsonl")
SUMMARIES_FILE = os.path.join(DATA_DIR, "game_summaries.jsonl")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "processed_ids.txt")
VECTOR_INDEX_FILE = os.path.join(DATA_DIR, "game_vectors.index")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Constants for review filtering
MIN_REVIEW_WORDS = 20
MAX_REVIEW_WORDS = 2000
MIN_CONFIDENCE_SCORE = 0.7
MAX_REVIEWS_PER_GAME = 100

# Review filtering patterns
RECIPE_INDICATORS = [
    'ingredients:', 
    'instructions:', 
    'preheat', 
    'cups of', 
    'tablespoons of',
    'mix until',
    'bake for'
]

ASCII_ART_PATTERNS = [
    r'([\W_])\1{10,}',
    r'[\/\\\|\-\=\+]{20,}',
    r'(.+\n)\1{3,}'
]

KNOWN_COPYPASTA_STARTS = [
    "my grandfather smoked his whole life",
    "what the fuck did you just fucking say about me",
    "according to all known laws of aviation"
]

OFF_TOPIC_INDICATORS = [
    'subscribe to my', 
    'check out my', 
    'follow me on',
    'trading cards',
    'free key',
    'giveaway',
    'trade offer'
]

GAME_RELATED_TERMS = {
    'play', 'game', 'level', 'character', 'story', 'graphics',
    'control', 'gameplay', 'multiplayer', 'single', 'player',
    'steam', 'hour', 'recommend', 'feature', 'mission'
}