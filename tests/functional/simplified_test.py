"""
Simplified functional tests for SteamSeek.
These tests verify that the key components work together without relying on template rendering.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

@pytest.mark.functional
class TestSimplifiedWorkflows:
    """Simplified tests for key user workflows."""
    
    @patch('firebase_config.firebase_auth')
    @patch('firebase_config.db')
    def test_auth_workflow(self, mock_db, mock_firebase_auth, client):
        """Test the authentication workflow."""
        
        # Setup mocks
        mock_user = MagicMock()
        mock_user.uid = "test-uid-123"
        mock_user.email = "user@example.com"
        
        # Set up Firebase auth mock for login
        mock_firebase_auth.sign_in_with_email_and_password.return_value = {
            "localId": mock_user.uid,
            "email": mock_user.email,
            "displayName": "Test User",
            "idToken": "test-id-token"
        }
        
        # 1. Manually set session data to simulate login
        with client.session_transaction() as session:
            session['user_id'] = mock_user.uid
        
        # 2. Log out
        logout_response = client.get('/logout')
        
        # 3. Check for redirect after logout
        assert logout_response.status_code == 302
        assert '/search' in logout_response.location or '/login' in logout_response.location
    
    @patch('blueprints.search.perform_search')
    def test_search_workflow(self, mock_perform_search, client):
        """Test the search workflow."""
        
        # Setup mocks
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
            }
        ]
        mock_explanation = "Test search explanation"
        mock_perform_search.return_value = (mock_results, mock_explanation)
        
        # Bypass template rendering to focus just on the API interaction
        with patch('flask.render_template', return_value="Mocked render"):
            # 1. Perform a basic search
            response = client.post('/search/execute', data={
                'query': 'action games',
                'genre': 'All',
                'year': 'All',
                'platform': 'All',
                'price': 'All',
                'sort_by': 'Relevance',
                'result_limit': '50'
            })
            
            # 2. Check for successful response
            assert response.status_code == 200
            
            # 3. Verify search was performed with correct parameters
            mock_perform_search.assert_called_once()
            args, kwargs = mock_perform_search.call_args
            assert args[0] == 'action games'
    
    @patch('flask_login.current_user')
    def test_list_management_workflow(self, mock_current_user, auth_client):
        """Test the list management workflow."""
        
        # Setup mocks
        mock_current_user.get_lists.return_value = [
            {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games', 'game_count': 2}
        ]
        mock_current_user.create_list.return_value = "new-list-id"
        mock_current_user.add_game_to_list.return_value = True
        mock_current_user.get_games_in_list.return_value = [
            {'appid': 123, 'name': 'Test Game 1', 'header_image': 'image1.jpg'}
        ]
        mock_current_user.id = "test-user-id"
        
        # Bypass template rendering
        with patch('flask.render_template', return_value="Mocked render"):
            # 1. View user lists
            lists_response = auth_client.get('/lists')
            assert lists_response.status_code == 200
            
            # 2. Create a new list
            create_response = auth_client.post('/create_list', data={
                'list_name': 'New Test List',
                'description': 'A test list'
            })
            # Check redirect after creation
            assert create_response.status_code == 302
            
            # 3. Add a game to the list
            add_game_response = auth_client.post('/save_game/789', data={
                'list_ids': ['new-list-id']
            })
            assert add_game_response.status_code == 200
            
            # 4. View the list with the added game
            view_list_response = auth_client.get('/list/new-list-id')
            assert view_list_response.status_code == 200
    
    @patch('flask_login.current_user')
    @patch('blueprints.games.get_game_data_by_appid')
    def test_game_interaction_workflow(self, mock_get_game, mock_current_user, auth_client):
        """Test the game interaction workflow."""
        
        # Setup mocks
        mock_game_data = {
            'appid': 123456,
            'name': 'Test Game',
            'short_description': 'A game for testing',
            'header_image': 'https://example.com/test_game.jpg',
            'screenshots': [{'path_full': 'https://example.com/screenshot1.jpg'}]
        }
        
        mock_current_user.get_game_note.return_value = None  # No notes initially
        mock_current_user.save_game_note.return_value = True
        mock_current_user.id = "test-user-id"
        mock_current_user.is_authenticated = True
        
        mock_get_game.return_value = mock_game_data
        
        # Bypass template rendering
        with patch('flask.render_template', return_value="Mocked render"):
            # 1. View game details page
            details_response = auth_client.get('/detail/123456')
            assert details_response.status_code == 200
            
            # 2. Add notes to the game
            notes_response = auth_client.post('/api/game_note/123456', json={
                'note': 'These are my test notes.'
            })
            assert notes_response.status_code == 200
            # Verify notes were saved correctly
            mock_current_user.save_game_note.assert_called_with('123456', 'These are my test notes.')

@pytest.mark.functional
class TestCrossComponentWorkflows:
    """Simplified tests for workflows that span multiple components."""
    
    @patch('flask_login.current_user')
    @patch('blueprints.search.perform_search')
    @patch('blueprints.games.get_game_data_by_appid')
    def test_search_to_list_workflow(self, mock_get_game, mock_perform_search, mock_current_user, auth_client):
        """Test workflow from search to adding game to list."""
        
        # Setup mocks
        mock_search_results = [
            {
                'appid': 123456,
                'name': 'Test Game 1',
                'media': ['https://example.com/image1.jpg'],
                'genres': ['Action', 'Adventure'],
                'release_year': '2023'
            }
        ]
        mock_perform_search.return_value = (mock_search_results, "Test explanation")
        
        mock_game_data = {
            'appid': 123456,
            'name': 'Test Game 1',
            'short_description': 'A game for testing',
            'header_image': 'https://example.com/test_game.jpg'
        }
        mock_get_game.return_value = mock_game_data
        
        mock_current_user.get_lists.return_value = [
            {'id': 'list1', 'name': 'My List', 'description': 'My games', 'game_count': 0}
        ]
        mock_current_user.add_game_to_list.return_value = True
        mock_current_user.id = "test-user-id"
        mock_current_user.is_authenticated = True
        
        # Bypass template rendering
        with patch('flask.render_template', return_value="Mocked render"):
            # 1. Perform a search
            search_response = auth_client.post('/search/execute', data={
                'query': 'test game',
                'genre': 'All',
                'year': 'All',
                'platform': 'All',
                'price': 'All',
                'sort_by': 'Relevance',
                'result_limit': '50'
            })
            assert search_response.status_code == 200
            
            # 2. View game details
            details_response = auth_client.get('/detail/123456')
            assert details_response.status_code == 200
            
            # 3. Add game to list
            add_to_list_response = auth_client.post('/save_game/123456', data={
                'list_ids': ['list1']
            })
            assert add_to_list_response.status_code == 200
            
            # Verify game was added to the list
            mock_current_user.add_game_to_list.assert_called()

@pytest.mark.performance
class TestPerformance:
    """Simplified performance tests."""
    
    @patch('blueprints.search.perform_search')
    def test_search_performance(self, mock_perform_search, client):
        """Test search performance."""
        
        # Setup mock
        mock_results = [{'appid': 123, 'name': 'Test Game'}]
        mock_perform_search.return_value = (mock_results, "Test explanation")
        
        # Bypass template rendering
        with patch('flask.render_template', return_value="Mocked render"):
            # Perform a search and verify it works
            response = client.post('/search/execute', data={
                'query': 'test game',
                'genre': 'All',
                'year': 'All',
                'platform': 'All',
                'price': 'All',
                'sort_by': 'Relevance'
            })
            assert response.status_code == 200
            
            # Verify search was called
            mock_perform_search.assert_called_once() 