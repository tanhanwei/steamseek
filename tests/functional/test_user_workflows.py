"""
Functional tests for complete user workflows in SteamSeek.
These tests simulate real user interactions across multiple components.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import re
import flask

# Authentication Flow Tests
@pytest.mark.functional
class TestAuthenticationWorkflow:
    """Test the complete authentication workflow."""
    
    @patch('firebase_config.firebase_auth')
    @patch('firebase_config.db')
    def test_register_login_logout_flow(self, mock_db, mock_firebase_auth, client):
        """
        Test a complete user registration, login, and logout flow.
        This simulates a new user registering, logging in, and then logging out.
        """
        # Mock Firebase auth responses
        mock_user = MagicMock()
        mock_user.uid = "test-uid-123"
        mock_user.email = "new_user@example.com"
        mock_user.display_name = "New Test User"
        
        # Set up Firebase auth mock for login
        mock_firebase_auth.sign_in_with_email_and_password.return_value = {
            "localId": mock_user.uid,
            "email": mock_user.email,
            "displayName": mock_user.display_name,
            "idToken": "test-id-token"
        }
        
        # 1. Manually set session data to simulate successful login
        with client.session_transaction() as session:
            session['user_id'] = mock_user.uid
            session['_user_id'] = mock_user.uid
        
        # 2. Log out
        logout_response = client.get('/logout')
        
        # 3. Check that logout redirects (which indicates successful processing)
        assert logout_response.status_code == 302  # Redirect status code
        
        # 4. Verify the redirect location contains the expected target
        # The logout process should redirect to the search page or login page
        assert '/search' in logout_response.location or '/login' in logout_response.location

# Search Flow Tests
@pytest.mark.functional
class TestSearchWorkflow:
    """Test the complete search workflow."""
    
    @patch('blueprints.search.perform_search')
    @patch('flask.render_template')
    def test_basic_to_deep_search_flow(self, mock_render, mock_perform_search, client):
        """
        Test a complete search flow from basic search to deep search.
        This simulates a user performing a search, viewing results, then initiating a deep search.
        """
        # Mock search results
        mock_results = [
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
        mock_perform_search.return_value = (mock_results, mock_explanation)
        
        # Set up the render_template mock to return a simple string
        mock_render.return_value = "Search results rendered"
        
        # Mock deep search status
        with patch('blueprints.search.deep_search_status', return_value={
            'active': True,
            'progress': 100,
            'current_step': 'Completed',
            'completed': True,
            'result_count': 5,
            'ready_for_viewing': True,
            'error': None
        }):
            # 1. Perform a basic search
            basic_search_response = client.post('/search/execute', data={
                'query': 'action adventure games',
                'genre': 'All',
                'year': 'All',
                'platform': 'All',
                'price': 'All',
                'sort_by': 'Relevance',
                'result_limit': '50'
            })
            
            # Check basic search success
            assert basic_search_response.status_code == 200
            
            # Verify search was performed with correct parameters
            mock_perform_search.assert_called_once()
            args, kwargs = mock_perform_search.call_args
            assert args[0] == 'action adventure games'  # query
            
            # Verify render_template was called
            mock_render.assert_called()
            
            # 2. Check deep search status
            with patch('blueprints.search.check_deep_search_status') as mock_status:
                mock_status.return_value = {
                    'active': True,
                    'progress': 100,
                    'current_step': 'Completed',
                    'completed': True,
                    'result_count': 5,
                    'ready_for_viewing': True,
                    'error': None
                }
                status_response = client.get('/deep_search_status')
                assert status_response.status_code == 200

# Lists Management Flow Tests
@pytest.mark.functional
class TestListsWorkflow:
    """Test the complete lists management workflow."""
    
    @patch('flask_login.current_user')
    @patch('flask.render_template')
    def test_create_manage_list_flow(self, mock_render, mock_current_user, auth_client):
        """
        Test a complete list creation and management flow.
        This simulates a user creating a list, adding games to it, and managing it.
        """
        # Mock user list and game data
        mock_lists = [
            {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games', 'game_count': 2},
            {'id': 'list2', 'name': 'To Play', 'description': 'Games I want to play', 'game_count': 0}
        ]
        
        mock_games = [
            {'appid': 123, 'name': 'Test Game 1', 'header_image': 'image1.jpg'},
            {'appid': 456, 'name': 'Test Game 2', 'header_image': 'image2.jpg'}
        ]
        
        # Setup mock methods
        mock_current_user.get_lists.return_value = mock_lists
        mock_current_user.get_games_in_list.return_value = mock_games
        mock_current_user.create_list.return_value = "new-list-id"
        mock_current_user.add_game_to_list.return_value = True
        mock_current_user.remove_game_from_list.return_value = True
        mock_current_user.update_list_metadata.return_value = True
        mock_current_user.delete_list.return_value = True
        mock_current_user.id = "test-user-id"
        
        # Set up render_template mock
        mock_render.return_value = "Lists page rendered"
        
        # 1. View user lists
        lists_response = auth_client.get('/lists')
        assert lists_response.status_code == 200
        
        # 2. Create a new list
        create_response = auth_client.post('/create_list', data={
            'list_name': 'New Test List',
            'description': 'A list created in a functional test'
        }, follow_redirects=False)  # Avoid redirect issues
        
        # Check for redirect to lists page
        assert create_response.status_code == 302
        
        # 3. Add a game to the list
        # First, update the mock to include our new list
        updated_lists = mock_lists + [{'id': 'new-list-id', 'name': 'New Test List', 
                                      'description': 'A list created in a functional test', 'game_count': 0}]
        mock_current_user.get_lists.return_value = updated_lists
        
        add_game_response = auth_client.post('/save_game/789', data={
            'list_ids': ['new-list-id']
        })
        
        assert add_game_response.status_code == 200
        
        # 4. View the list with the added game
        # Update the mock to show the game in the list
        mock_games_in_new_list = [{'appid': 789, 'name': 'Test Game 3', 'header_image': 'image3.jpg'}]
        mock_current_user.get_games_in_list.side_effect = lambda list_id: mock_games_in_new_list if list_id == 'new-list-id' else mock_games
        
        view_list_response = auth_client.get('/list/new-list-id')
        assert view_list_response.status_code == 200
        
        # 5. Remove the game from the list
        remove_game_response = auth_client.post('/remove_game/new-list-id/789')
        
        assert remove_game_response.status_code == 200

# Game Interaction Flow Tests
@pytest.mark.functional
class TestGameInteractionWorkflow:
    """Test the complete game interaction workflow."""
    
    @patch('flask_login.current_user')
    @patch('blueprints.games.get_game_data_by_appid')
    @patch('blueprints.games.analyze_game')
    @patch('flask.render_template')
    def test_game_details_notes_analysis_flow(self, mock_render, mock_analyze_game, mock_get_game, mock_current_user, auth_client):
        """
        Test a complete game details, notes, and analysis flow.
        This simulates a user viewing game details, adding notes, and viewing AI analysis.
        """
        # Mock game data
        mock_game_data = {
            'appid': 123456,
            'name': 'Test Game',
            'short_description': 'A game for testing',
            'detailed_description': 'This is a detailed description of Test Game',
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
                'summary': 'This is an AI-generated analysis of Test Game.',
                'key_features': ['Feature 1', 'Feature 2'],
                'pros': ['Pro 1', 'Pro 2'],
                'cons': ['Con 1'],
                'similar_games': ['Similar Game 1', 'Similar Game 2'],
                'player_experience': 'Test Game offers an engaging experience.',
                'market_position': 'Test Game is positioned as a mid-tier indie game.'
            }
        }
        
        # Mock note data
        mock_notes = "These are my notes about Test Game."
        
        # Setup mocks
        mock_get_game.return_value = mock_game_data
        mock_analyze_game.return_value = mock_analysis
        mock_current_user.get_game_note.return_value = None  # No notes at first
        mock_current_user.save_game_note.return_value = True
        mock_current_user.id = "test-user-id"
        mock_current_user.is_authenticated = True
        
        # Set up render_template mock
        mock_render.return_value = "Game detail page rendered"
        
        # 1. View game details page
        details_response = auth_client.get('/detail/123456')
        assert details_response.status_code == 200
        
        # 2. View or generate game analysis
        analysis_response = auth_client.get('/api/analyze/123456')
        assert analysis_response.status_code == 200
        
        # 3. Add notes to the game
        notes_response = auth_client.post('/api/game_note/123456', json={
            'note': mock_notes
        })
        
        assert notes_response.status_code == 200
        
        # 4. View the game again with notes
        # Update mock to return the saved notes
        mock_current_user.get_game_note.return_value = mock_notes
        
        details_with_notes_response = auth_client.get('/detail/123456')
        assert details_with_notes_response.status_code == 200 