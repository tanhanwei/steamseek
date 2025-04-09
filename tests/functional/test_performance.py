"""
Performance tests for SteamSeek application.
These tests measure the performance of key operations across components.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
import json

@pytest.mark.performance
class TestSearchPerformance:
    """Test the performance of search operations."""
    
    @patch('blueprints.search.perform_search')
    def test_basic_search_performance(self, mock_perform_search, client):
        """
        Test the performance of basic search operations.
        This measures response time for typical search requests.
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
            }
        ]
        mock_explanation = "Test search explanation"
        
        # Have the mock wait a consistent time before returning to simulate processing
        def delayed_response(*args, **kwargs):
            # Simulate some processing time
            time.sleep(0.05)
            return (mock_results, mock_explanation)
        
        mock_perform_search.side_effect = delayed_response
        
        # Performance test parameters
        num_iterations = 10
        max_acceptable_avg_time = 0.5  # Maximum acceptable average response time in seconds
        timings = []
        
        # Run multiple search iterations to gather performance data
        for i in range(num_iterations):
            start_time = time.time()
            
            response = client.post('/search/execute', data={
                'query': f'test query {i}',
                'genre': 'All',
                'year': 'All',
                'platform': 'All',
                'price': 'All',
                'sort_by': 'Relevance',
                'result_limit': '50'
            })
            
            end_time = time.time()
            
            # Verify the search was successful
            assert response.status_code == 200
            
            # Record timing
            elapsed_time = end_time - start_time
            timings.append(elapsed_time)
        
        # Calculate performance metrics
        avg_time = sum(timings) / len(timings)
        max_time = max(timings)
        min_time = min(timings)
        
        # Performance assertions
        assert avg_time < max_acceptable_avg_time, f"Average search time ({avg_time:.3f}s) exceeds acceptable limit ({max_acceptable_avg_time}s)"
        
        # Log performance metrics for reporting
        print(f"\nSearch Performance Results:")
        print(f"  Average Time: {avg_time:.3f}s")
        print(f"  Maximum Time: {max_time:.3f}s")
        print(f"  Minimum Time: {min_time:.3f}s")


@pytest.mark.performance
class TestGameDetailsPerformance:
    """Test the performance of game details operations."""
    
    @patch('blueprints.games.get_game_data_by_appid')
    def test_game_details_performance(self, mock_get_game, client):
        """
        Test the performance of game details page rendering.
        This measures response time for game detail requests.
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
        
        # Setup mock
        mock_get_game.return_value = mock_game_data
        
        # Performance test parameters
        num_iterations = 10
        max_acceptable_avg_time = 0.3  # Maximum acceptable average response time in seconds
        timings = []
        
        # Run multiple detail page requests to gather performance data
        for i in range(num_iterations):
            start_time = time.time()
            
            response = client.get('/detail/123456')
            
            end_time = time.time()
            
            # Verify the request was successful
            assert response.status_code == 200
            
            # Record timing
            elapsed_time = end_time - start_time
            timings.append(elapsed_time)
        
        # Calculate performance metrics
        avg_time = sum(timings) / len(timings)
        max_time = max(timings)
        min_time = min(timings)
        
        # Performance assertions
        assert avg_time < max_acceptable_avg_time, f"Average game details time ({avg_time:.3f}s) exceeds acceptable limit ({max_acceptable_avg_time}s)"
        
        # Log performance metrics for reporting
        print(f"\nGame Details Performance Results:")
        print(f"  Average Time: {avg_time:.3f}s")
        print(f"  Maximum Time: {max_time:.3f}s")
        print(f"  Minimum Time: {min_time:.3f}s")


@pytest.mark.performance
class TestListsPerformance:
    """Test the performance of lists operations."""
    
    @patch('flask_login.current_user')
    def test_lists_view_performance_with_scaling_items(self, mock_current_user, auth_client):
        """
        Test the performance of lists view as the number of items increases.
        This measures how the application scales with larger lists.
        """
        # Create mock user data
        mock_current_user.id = "test-user-id"
        mock_current_user.is_authenticated = True
        
        # Lists to test with increasing size
        list_sizes = [10, 50, 100]
        max_acceptable_times = {
            10: 0.2,   # 10 items should be < 0.2s
            50: 0.4,   # 50 items should be < 0.4s
            100: 0.8,  # 100 items should be < 0.8s
        }
        
        for size in list_sizes:
            # Create mock list data with 'size' number of games
            mock_games = []
            for i in range(size):
                mock_games.append({
                    'appid': 1000 + i,
                    'name': f'Test Game {i}',
                    'header_image': f'https://example.com/image{i}.jpg'
                })
            
            # Setup mock
            mock_current_user.get_lists.return_value = [
                {'id': 'test_list', 'name': f'Test List ({size} games)', 
                 'description': 'Performance test list', 'game_count': size}
            ]
            mock_current_user.get_games_in_list.return_value = mock_games
            
            # Measure list view performance
            start_time = time.time()
            
            response = auth_client.get('/list/test_list')
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Verify the request was successful
            assert response.status_code == 200
            
            # Check performance for this list size
            max_time = max_acceptable_times[size]
            assert elapsed_time < max_time, f"List view with {size} items took {elapsed_time:.3f}s, exceeding limit of {max_time}s"
            
            # Log performance result
            print(f"\nList View Performance ({size} items):")
            print(f"  Time: {elapsed_time:.3f}s (Limit: {max_time}s)")


@pytest.mark.performance
class TestAuthPerformance:
    """Test the performance of authentication operations."""
    
    @patch('firebase_config.firebase_auth')
    def test_login_performance(self, mock_firebase_auth, client):
        """
        Test the performance of login operations.
        This measures response time for authentication requests.
        """
        # Mock Firebase auth response
        mock_firebase_auth.sign_in_with_email_and_password.return_value = {
            "localId": "test-uid-123",
            "email": "test@example.com",
            "displayName": "Test User",
            "idToken": "test-id-token"
        }
        
        # Performance test parameters
        num_iterations = 10
        max_acceptable_avg_time = 0.3  # Maximum acceptable average response time in seconds
        timings = []
        
        # Run multiple login attempts to gather performance data
        for i in range(num_iterations):
            start_time = time.time()
            
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            end_time = time.time()
            
            # We don't check status code because it will redirect; that's expected
            
            # Record timing
            elapsed_time = end_time - start_time
            timings.append(elapsed_time)
        
        # Calculate performance metrics
        avg_time = sum(timings) / len(timings)
        max_time = max(timings)
        min_time = min(timings)
        
        # Performance assertions
        assert avg_time < max_acceptable_avg_time, f"Average login time ({avg_time:.3f}s) exceeds acceptable limit ({max_acceptable_avg_time}s)"
        
        # Log performance metrics for reporting
        print(f"\nLogin Performance Results:")
        print(f"  Average Time: {avg_time:.3f}s")
        print(f"  Maximum Time: {max_time:.3f}s")
        print(f"  Minimum Time: {min_time:.3f}s") 