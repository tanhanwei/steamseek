from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import json
from data_loader import get_game_data_by_appid

# Create the blueprint
lists_bp = Blueprint('lists', __name__, template_folder='templates')

@lists_bp.route('/lists')
@login_required
def user_lists():
    """
    Display the user's game lists
    """
    user_lists = current_user.get_lists()
    return render_template('lists.html', lists=user_lists)

@lists_bp.route('/list/<list_id>')
@login_required
def view_list(list_id):
    """
    View a specific list's details
    """
    # Get the list info
    user_lists = current_user.get_lists()
    list_info = None
    for lst in user_lists:
        if lst['id'] == list_id:
            list_info = lst
            break
            
    if not list_info:
        flash('List not found', 'error')
        return redirect(url_for('lists.user_lists'))
        
    # Get games in the list
    games = current_user.get_games_in_list(list_id)
    
    return render_template(
        'list_detail.html', 
        list_id=list_id, 
        list_info=list_info, 
        games=games
    )

@lists_bp.route('/create_list', methods=['POST'])
@login_required
def create_list():
    """
    Create a new list
    """
    list_name = request.form.get('list_name', '').strip()
    if not list_name:
        flash('List name cannot be empty', 'error')
        return redirect(url_for('lists.user_lists'))
        
    list_id = current_user.create_list(list_name)
    if list_id:
        flash(f'List "{list_name}" created successfully', 'success')
    else:
        flash('Failed to create list', 'error')
        
    return redirect(url_for('lists.user_lists'))

@lists_bp.route('/api/game_lists/<appid>')
@login_required
def get_game_lists(appid):
    """
    Get all lists for a specific game
    """
    game_lists = current_user.get_game_lists(appid)
    all_lists = current_user.get_lists()
    
    response = {
        'in_lists': game_lists,
        'all_lists': all_lists
    }
    
    return jsonify(response)

@lists_bp.route('/save_game/<appid>', methods=['POST'])
@login_required
def save_game(appid):
    """
    Save a game to one or more lists
    """
    try:
        # Get the target list IDs
        if request.is_json:
            data = request.get_json()
            list_ids = data.get('list_ids', [])
        else:
            list_ids = request.form.getlist('list_ids')
            
        if not list_ids:
            return jsonify({
                "success": False,
                "message": "No lists selected"
            })
            
        # Get game data
        appid = int(appid)
        STEAM_DATA_FILE = current_app.config.get('STEAM_DATA_FILE', "data/steam_games_data.jsonl")
        index_map = current_app.config.get('index_map')
        
        game_data = get_game_data_by_appid(appid, STEAM_DATA_FILE, index_map)
        if not game_data:
            return jsonify({
                "success": False,
                "message": f"Game with ID {appid} not found"
            })
            
        # Prepare game data for storage
        game_to_save = {
            "appid": appid,
            "name": game_data.get("name", "Unknown Game"),
            "header_image": game_data.get("header_image", ""),
            "short_description": game_data.get("short_description", "")
        }
        
        # Save to each selected list
        success_count = 0
        for list_id in list_ids:
            if current_user.add_game_to_list(list_id, game_to_save):
                success_count += 1
                
        if success_count == 0:
            return jsonify({
                "success": False,
                "message": "Failed to save game to any lists"
            })
        elif success_count < len(list_ids):
            return jsonify({
                "success": True,
                "message": f"Game saved to {success_count} out of {len(list_ids)} lists"
            })
        else:
            return jsonify({
                "success": True,
                "message": "Game saved successfully to all selected lists"
            })
            
    except Exception as e:
        current_app.logger.error(f"Error saving game: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Error saving game: {str(e)}"
        })

@lists_bp.route('/remove_game/<list_id>/<appid>', methods=['POST'])
@login_required
def remove_game(list_id, appid):
    """
    Remove a game from a list
    """
    try:
        appid = int(appid)
        
        if current_user.remove_game_from_list(list_id, appid):
            return jsonify({
                "success": True,
                "message": "Game removed from list successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to remove game from list"
            })
    except Exception as e:
        current_app.logger.error(f"Error removing game: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Error removing game: {str(e)}"
        })

@lists_bp.route('/api/update_list/<list_id>', methods=['POST'])
@login_required
def update_list(list_id):
    """
    Update list metadata (name, description, notes)
    """
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        if not field or not value:
            return jsonify({
                "success": False,
                "message": "Missing field or value"
            })
            
        if field not in ['name', 'description', 'notes']:
            return jsonify({
                "success": False,
                "message": f"Invalid field: {field}"
            })
            
        if current_user.update_list_metadata(list_id, field, value):
            return jsonify({
                "success": True,
                "message": f"List {field} updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Failed to update list {field}"
            })
            
    except Exception as e:
        current_app.logger.error(f"Error updating list: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Error updating list: {str(e)}"
        })

@lists_bp.route('/api/save_results_as_list', methods=['POST'])
@login_required
def save_results_as_list():
    """
    Save search results as a new list
    """
    try:
        data = request.get_json()
        list_name = data.get('list_name', '').strip()
        results = data.get('results', [])
        
        if not list_name:
            return jsonify({
                "success": False,
                "message": "List name cannot be empty"
            })
            
        if not results:
            return jsonify({
                "success": False,
                "message": "No results to save"
            })
            
        # Create the new list
        list_id = current_user.create_list(list_name)
        if not list_id:
            return jsonify({
                "success": False,
                "message": "Failed to create list"
            })
            
        # Add each game to the list
        for game in results:
            game_to_save = {
                "appid": game.get("appid"),
                "name": game.get("name", "Unknown Game"),
                "header_image": game.get("media", [])[0] if game.get("media") else "",
                "short_description": game.get("ai_summary", "")[:200] + "..." if len(game.get("ai_summary", "")) > 200 else game.get("ai_summary", "")
            }
            current_user.add_game_to_list(list_id, game_to_save)
            
        return jsonify({
            "success": True,
            "message": f"Created list '{list_name}' with {len(results)} games",
            "list_id": list_id
        })
            
    except Exception as e:
        current_app.logger.error(f"Error creating list from results: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Error saving results as list: {str(e)}"
        }) 