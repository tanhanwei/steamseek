from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from markupsafe import Markup
import os
import json
import logging
import markdown
import time
from collections import OrderedDict
import uuid

# Import Firebase and Flask-Login 
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from firebase_config import User, firebase_auth, db

# Import our data loader and helper functions
from data_loader import build_steam_data_index, load_summaries, get_game_data_by_appid
from game_chatbot import semantic_search_query
from llm_processor import OPENROUTER_API_KEY

# Import blueprints
from blueprints.search import search_bp
from blueprints.auth import auth_bp
from blueprints.lists import lists_bp
from blueprints.games import games_bp

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key")  # Required for session support

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Update to use the auth blueprint

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Configure logging
if not app.debug:
    pass
else:
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

# Custom Jinja filter to render markdown as HTML
def markdown_filter(text):
    if not text:
        return ""
    try:
        return Markup(markdown.markdown(text))
    except Exception as e:
        print(f"Error rendering markdown: {e}")
        return Markup(f"<p>Error rendering markdown: {e}</p><pre>{text}</pre>")
app.jinja_env.filters['markdown'] = markdown_filter

# Define file paths
STEAM_DATA_FILE = "data/steam_games_data.jsonl"
SUMMARIES_FILE = "data/summaries.jsonl"
ANALYSIS_CACHE_FILE = "data/analysis_cache.jsonl"

# TESTING flag for development
TESTING_ENABLE_SYNTHETIC_SUMMARIES = True

# Build the index map once at startup and store in app.config
# so it can be accessed by blueprints
logging.basicConfig(level=logging.INFO)
index_map = build_steam_data_index(STEAM_DATA_FILE)
app.config['index_map'] = index_map  # Store in app config for blueprint access
app.config['STEAM_DATA_FILE'] = STEAM_DATA_FILE  # Store file paths in config
app.config['SUMMARIES_FILE'] = SUMMARIES_FILE
app.config['ANALYSIS_CACHE_FILE'] = ANALYSIS_CACHE_FILE

# Register blueprints
app.register_blueprint(search_bp, url_prefix='')
app.register_blueprint(auth_bp, url_prefix='')
app.register_blueprint(lists_bp, url_prefix='')
app.register_blueprint(games_bp, url_prefix='')

# Redirect root to search page
@app.route('/')
def index():
    return redirect(url_for('search.search_page'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 