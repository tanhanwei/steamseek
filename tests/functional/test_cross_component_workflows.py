"""
Functional tests for cross-component workflows in SteamSeek.
These tests simulate complex user interactions that span multiple system components.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

@pytest.mark.functional
class TestCrossComponentWorkflows:
    """Test workflows that span multiple system components."""
    
    @patch('flask_login.current_user')
    @patch('blueprints.search.perform_search')
    @patch('blueprints.games.get_game_data_by_appid')
    @patch('blueprints.games.analyze_game')
    @patch('flask.render_template')
    def test_search_to_game_detail_to_list_flow(
        self, mock_render, mock_analyze_game, mock_get_game,
        mock_perform_search, mock_current_user, auth_client
    ):
        """
        Test a complete workflow from search to game detail to adding to list.
        This simulates a user searching for games, viewing details, and adding to a list.
        """
        # Mock search results
        mock_search_results = [
            {
                'appid': 123456,
                'name': 'Test Game 1',
                'media': ['https://example.com/image1.jpg'],
                'genres': ['Action', 'Adventure'],
                'release_year': '2023',
                'platforms': {'windows': True, 'mac': False, 'linux': False},
                'is_free': False,
                'price': 19.99,
                'pos_percent': 85,
                'total_reviews': 100,
                'ai_summary': 'A test game about testing'
            },
            {
                'appid': 234567,
                'name': 'Test Game 2',
                'media': ['https://example.com/image2.jpg'],
                'genres': ['RPG', 'Strategy'],
                'release_year': '2022',
                'platforms': {'windows': True, 'mac': True, 'linux': False},
                'is_free': True,
                'price': 0.0,
                'pos_percent': 90,
                'total_reviews': 200,
                'ai_summary': 'Another test game'
            }
        ]
        mock_explanation = "This is a test search explanation"
        mock_perform_search.return_value = (mock_search_results, mock_explanation)
        
        # Mock game data
        mock_game_data = {
            'appid': 123456,
            'name': 'Test Game 1',
            'short_description': 'A game for testing',
            'detailed_description': 'This is a detailed description of Test Game 1',
            'header_image': 'https://example.com/test_game.jpg',
            'screenshots': [{'path_full': 'https://example.com/screenshot1.jpg'}],
            'release_date': {'date': '15 Jan, 2023'},
            'developers': ['Test Developer'],
            'publishers': ['Test Publisher'],
            'genres': [{'description': 'Action'}, {'description': 'Adventure'}],
            'price_overview': {'final_formatted': '$19.99'},
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'metacritic': {'score': 85},
            'categories': [{'description': 'Single-player'}, {'description': 'Multi-player'}],
            'recommendations': {'total': 1000}
        }
        
        # Mock analysis data
        mock_analysis = {
            'success': True,
            'analysis': {
                'summary': 'This is an AI-generated analysis of Test Game 1.',
                'key_features': ['Feature 1', 'Feature 2'],
                'pros': ['Pro 1', 'Pro 2'],
                'cons': ['Con 1'],
                'similar_games': ['Similar Game 1', 'Similar Game 2'],
                'player_experience': 'Test Game 1 offers an engaging experience.',
                'market_position': 'Test Game 1 is positioned as a mid-tier indie game.'
            }
        }
        
        # Mock user lists
        mock_lists = [
            {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games', 'game_count': 2},
            {'id': 'list2', 'name': 'To Play', 'description': 'Games I want to play', 'game_count': 0}
        ]
        
        # Setup mocks
        mock_get_game.return_value = mock_game_data
        mock_analyze_game.return_value = mock_analysis
        mock_current_user.get_lists.return_value = mock_lists
        mock_current_user.add_game_to_list.return_value = True
        mock_current_user.id = "test-user-id"
        mock_current_user.is_authenticated = True
        
        # Set up render_template mock
        mock_render.return_value = "Page rendered"
        
        # 1. User performs a search
        search_response = auth_client.post('/search/execute', data={
            'query': 'action adventure games',
            'genre': 'All',
            'year': 'All',
            'platform': 'All',
            'price': 'All',
            'sort_by': 'Relevance',
            'result_limit': '50'
        })
        
        # Check search success
        assert search_response.status_code == 200
        
        # 2. User clicks on a game to view details
        details_response = auth_client.get('/detail/123456')
        assert details_response.status_code == 200
        
        # 3. User views game analysis
        analysis_response = auth_client.get('/api/analyze/123456')
        assert analysis_response.status_code == 200
        
        # 4. User adds the game to a list
        add_to_list_response = auth_client.post('/save_game/123456', data={
            'list_ids': ['list1']
        })
        
        assert add_to_list_response.status_code == 200
        
        # 5. User views the list to confirm the game was added
        # First update the mock to include games from the list
        mock_games_in_list = [
            {'appid': 123, 'name': 'Existing Game 1', 'header_image': 'image1.jpg'},
            {'appid': 456, 'name': 'Existing Game 2', 'header_image': 'image2.jpg'},
            {'appid': 123456, 'name': 'Test Game 1', 'header_image': 'https://example.com/test_game.jpg'}
        ]
        mock_current_user.get_games_in_list.return_value = mock_games_in_list
        
        view_list_response = auth_client.get('/list/list1')
        assert view_list_response.status_code == 200
    
    @patch('flask_login.current_user')
    @patch('blueprints.search.check_deep_search_status')
    @patch('flask.render_template')
    def test_deep_search_to_multiple_lists_flow(
        self, mock_render, mock_status, mock_current_user, auth_client
    ):
        """
        Test a workflow from deep search to adding games to multiple lists.
        This simulates a user performing a deep search and organizing results into different lists.
        """
        # Mock deep search status
        mock_status.return_value = json.dumps({
            'active': True,
            'progress': 100,
            'current_step': 'Completed',
            'completed': True,
            'result_count': 5,
            'ready_for_viewing': True,
            'error': None
        })
        
        # Mock user lists
        mock_lists = [
            {'id': 'action_list', 'name': 'Action Games', 'description': 'Action games collection', 'game_count': 5},
            {'id': 'rpg_list', 'name': 'RPG Games', 'description': 'RPG games to try', 'game_count': 2},
            {'id': 'simulation_list', 'name': 'Simulation Games', 'description': 'My simulation games', 'game_count': 1}
        ]
        
        # Setup mocks
        mock_current_user.get_lists.return_value = mock_lists
        mock_current_user.add_game_to_list.return_value = True
        mock_current_user.id = "test-user-id"
        mock_current_user.is_authenticated = True
        
        # Set up render_template mock
        mock_render.return_value = "Page rendered"
        
        # 1. User checks deep search status
        status_response = auth_client.get('/deep_search_status')
        assert status_response.status_code == 200
        
        # 2. User adds games to different lists
        # Add action game to action list
        add_action_response = auth_client.post('/save_game/123456', data={
            'list_ids': ['action_list']
        })
        assert add_action_response.status_code == 200
        
        # Add RPG game to RPG list
        add_rpg_response = auth_client.post('/save_game/234567', data={
            'list_ids': ['rpg_list']
        })
        assert add_rpg_response.status_code == 200
        
        # Add simulation game to simulation list
        add_sim_response = auth_client.post('/save_game/345678', data={
            'list_ids': ['simulation_list']
        })
        assert add_sim_response.status_code == 200
        
        # 3. User views all lists to confirm games were added
        # Setup mock to return different games for different lists
        def get_games_by_list(list_id):
            if list_id == 'action_list':
                return [
                    {'appid': 111, 'name': 'Existing Action Game', 'header_image': 'action.jpg'},
                    {'appid': 123456, 'name': 'Deep Search Game 1', 'header_image': 'https://example.com/ds_image1.jpg'}
                ]
            elif list_id == 'rpg_list':
                return [
                    {'appid': 222, 'name': 'Existing RPG Game', 'header_image': 'rpg.jpg'},
                    {'appid': 234567, 'name': 'Deep Search Game 2', 'header_image': 'https://example.com/ds_image2.jpg'}
                ]
            elif list_id == 'simulation_list':
                return [
                    {'appid': 345678, 'name': 'Deep Search Game 3', 'header_image': 'https://example.com/ds_image3.jpg'}
                ]
            return []
        
        mock_current_user.get_games_in_list.side_effect = get_games_by_list
        
        # Check action list
        action_list_response = auth_client.get('/list/action_list')
        assert action_list_response.status_code == 200
        
        # Check RPG list
        rpg_list_response = auth_client.get('/list/rpg_list')
        assert rpg_list_response.status_code == 200
        
        # Check simulation list
        sim_list_response = auth_client.get('/list/simulation_list')
        assert sim_list_response.status_code == 200 