from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
import json
import markdown
import os
from markupsafe import Markup

from data_loader import get_game_data_by_appid
from llm_processor import generate_game_analysis

# Create the blueprint
games_bp = Blueprint('games', __name__, template_folder='templates')

# Load analysis cache
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
                    current_app.logger.warning(f"Error parsing analysis cache line: {e}")
    return cache

def save_analysis_cache(cache: dict, file_path: str):
    """Save the detailed analysis cache to an external file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for analysis in cache.values():
                f.write(json.dumps(analysis) + "\n")
    except Exception as e:
        current_app.logger.error(f"Error saving analysis cache: {e}")

# Game analysis cache for dashboard
analysis_cache = {}

@games_bp.route('/detail/<appid>')
def game_detail(appid):
    """
    Display details for a specific game
    """
    global analysis_cache
    
    try:
        appid = int(appid)
        
        # Load the index map from app config
        index_map = current_app.config.get('index_map')
        STEAM_DATA_FILE = current_app.config.get('STEAM_DATA_FILE', "data/steam_games_data.jsonl")
        ANALYSIS_CACHE_FILE = current_app.config.get('ANALYSIS_CACHE_FILE', "data/analysis_cache.jsonl")
        
        # Lazy load the analysis cache if needed
        if not analysis_cache:
            analysis_cache = load_analysis_cache(ANALYSIS_CACHE_FILE)
            current_app.logger.info(f"Loaded {len(analysis_cache)} game analyses from cache")
            
        game_data = get_game_data_by_appid(appid, STEAM_DATA_FILE, index_map)
        if not game_data:
            return render_template('error.html', message=f"Game with ID {appid} not found")
        
        # Retrieve existing analysis if available
        analysis = None
        if appid in analysis_cache:
            analysis = analysis_cache[appid]
            
        # Get user's note for this game if logged in
        note = ""
        if current_user.is_authenticated:
            note = current_user.get_game_note(appid)
            
        return render_template('detail.html', game=game_data, analysis=analysis, note=note)
    except ValueError:
        return render_template('error.html', message="Invalid game ID")

@games_bp.route('/api/analyze/<appid>')
def analyze_game(appid):
    """
    Generate or retrieve AI analysis for a game
    """
    global analysis_cache
    
    try:
        appid = int(appid)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Load data paths from app config
        STEAM_DATA_FILE = current_app.config.get('STEAM_DATA_FILE', "data/steam_games_data.jsonl") 
        ANALYSIS_CACHE_FILE = current_app.config.get('ANALYSIS_CACHE_FILE', "data/analysis_cache.jsonl")
        index_map = current_app.config.get('index_map')
        
        # Lazy load the analysis cache if needed
        if not analysis_cache:
            analysis_cache = load_analysis_cache(ANALYSIS_CACHE_FILE)
        
        # Check cache first if not forcing refresh
        if not force_refresh and appid in analysis_cache:
            return jsonify({
                "success": True,
                "analysis": analysis_cache[appid],
                "source": "cache"
            })
            
        # Get game data
        game_data = get_game_data_by_appid(appid, STEAM_DATA_FILE, index_map)
        if not game_data:
            return jsonify({
                "success": False,
                "message": f"Game with ID {appid} not found"
            })
            
        # Generate the analysis
        analysis = generate_game_analysis(game_data)
        
        # Cache the analysis
        if analysis:
            # Add the appid to the analysis for storage
            analysis["appid"] = appid
            analysis_cache[appid] = analysis
            
            # Save to cache file
            save_analysis_cache(analysis_cache, ANALYSIS_CACHE_FILE)
            
        return jsonify({
            "success": True,
            "analysis": analysis,
            "source": "fresh"
        })
    except Exception as e:
        current_app.logger.error(f"Error analyzing game: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Error analyzing game: {str(e)}"
        })

@games_bp.route('/api/game_note/<appid>', methods=['GET', 'POST', 'DELETE'])
@login_required
def game_note(appid):
    """
    Handle CRUD operations for game notes
    """
    try:
        appid = int(appid)
        
        # GET request - retrieve note
        if request.method == 'GET':
            note = current_user.get_game_note(appid)
            return jsonify({
                "success": True,
                "note": note
            })
            
        # POST request - save note
        elif request.method == 'POST':
            data = request.get_json()
            note_text = data.get('note', '').strip()
            
            if current_user.save_game_note(appid, note_text):
                return jsonify({
                    "success": True,
                    "message": "Note saved successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Failed to save note"
                })
                
        # DELETE request - delete note
        elif request.method == 'DELETE':
            if current_user.delete_game_note(appid):
                return jsonify({
                    "success": True,
                    "message": "Note deleted successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Failed to delete note"
                })
    except Exception as e:
        current_app.logger.error(f"Error processing note: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Error processing note: {str(e)}"
        })

@games_bp.route('/api/render_markdown', methods=['POST'])
def render_markdown():
    """
    Render markdown to HTML
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        html = markdown.markdown(text)
        return jsonify({
            "success": True,
            "html": html
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error rendering markdown: {str(e)}"
        }) 