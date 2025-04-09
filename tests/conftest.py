"""
Test fixtures for SteamSeek tests.
"""
import pytest
from flask import Flask
from flask_login import LoginManager
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to sys.path so we can import from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Flask app
from app_refactored import app as flask_app


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Configure app for testing
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'DEBUG': False,
        'WTF_CSRF_ENABLED': False
    })
    
    # Mock Firebase and other external services
    with patch('firebase_config.db') as mock_db:
        with patch('firebase_config.firebase_auth') as mock_firebase_auth:
            with patch('firebase_config.firestore.SERVER_TIMESTAMP') as mock_timestamp:
                # Create a simple lookup map for app testing if not already set
                if 'index_map' not in flask_app.config:
                    flask_app.config['index_map'] = {}
                
                # Return the app for testing
                with flask_app.app_context():
                    yield flask_app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client(app):
    """Create an authenticated test client."""
    from firebase_config import User
    
    # Create a mock user
    mock_user = MagicMock(spec=User)
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.display_name = "Test User"
    
    with app.test_client() as client:
        # Mock the login_manager.current_user
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Set up a session for the authenticated user
            with client.session_transaction() as sess:
                sess['user_id'] = "test-user-id"
            
            yield client


@pytest.fixture
def app_context(app):
    """Provide an application context for tests that need Flask context."""
    with app.app_context():
        with app.test_request_context():
            yield


@pytest.fixture
def list_test_client(app, auth_client):
    """
    Specialized fixture for list testing that handles Flask context properly
    and pre-configures common mocks.
    """
    from firebase_config import User
    
    # Create a standard lists setup
    test_lists = [
        {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games'},
        {'id': 'list2', 'name': 'To Play', 'description': 'Games I want to play'}
    ]
    
    # Create test games
    test_games = [
        {'appid': 123, 'name': 'Test Game 1', 'header_image': 'image1.jpg'},
        {'appid': 456, 'name': 'Test Game 2', 'header_image': 'image2.jpg'}
    ]
    
    with patch('flask_login.current_user') as mock_current_user:
        # Set up common list-related methods
        mock_current_user.get_lists.return_value = test_lists
        mock_current_user.get_games_in_list.return_value = test_games
        mock_current_user.get_game_lists.return_value = [test_lists[0]]  # First list contains the game
        
        # For methods that modify data, default to success
        mock_current_user.create_list.return_value = "new-list-id"
        mock_current_user.add_game_to_list.return_value = True
        mock_current_user.remove_game_from_list.return_value = True
        mock_current_user.update_list_metadata.return_value = True
        
        yield auth_client, mock_current_user


@pytest.fixture
def mock_search_data():
    """Create mock search data for testing."""
    return [
        {
            "appid": 123,
            "name": "Test Game 1",
            "media": ["https://example.com/image1.jpg"],
            "genres": ["Action", "Adventure"],
            "release_year": "2020",
            "platforms": {"windows": True, "mac": False, "linux": False},
            "is_free": False,
            "price": 19.99,
            "pos_percent": 85,
            "total_reviews": 100,
            "ai_summary": "This is a test game summary."
        },
        {
            "appid": 456,
            "name": "Test Game 2",
            "media": ["https://example.com/image2.jpg"],
            "genres": ["RPG", "Strategy"],
            "release_year": "2019",
            "platforms": {"windows": True, "mac": True, "linux": True},
            "is_free": True,
            "price": 0.0,
            "pos_percent": 95,
            "total_reviews": 200,
            "ai_summary": "This is another test game summary."
        }
    ]


@pytest.fixture
def mock_render_template():
    """
    Mock Flask's render_template function to prevent URL generation issues during testing.
    
    This fixture allows tests to run without needing to generate valid URLs for templates,
    which can cause issues when endpoint names change or when context is not properly setup.
    """
    with patch('flask.render_template') as mock_render:
        # Make the mock return a simple string with the template name and context
        mock_render.side_effect = lambda template_name, **context: f"Mock rendered {template_name}"
        yield mock_render


@pytest.fixture
def runner(app):
    """
    Create a test CLI runner for the app.
    """
    return app.test_cli_runner()


@pytest.fixture
def mock_data():
    """
    Provide mock data for tests.
    """
    return {
        'sample_game': {
            'appid': 123456,
            'name': 'Test Game',
            'short_description': 'A game for testing',
            'header_image': 'https://example.com/image.jpg',
            'release_date': '2023',
            'store_data': {
                'platforms': {'windows': True, 'mac': False, 'linux': False},
                'is_free': False,
                'price_overview': {'final': 1999}  # $19.99
            },
            'reviews': [
                {'voted_up': True, 'review': 'Great game!'},
                {'voted_up': True, 'review': 'Awesome!'},
                {'voted_up': False, 'review': 'Not my style.'}
            ]
        },
        'sample_search_results': [
            {
                'appid': 123456,
                'name': 'Test Game 1',
                'ai_summary': 'A test game about testing',
                'similarity_score': 0.95
            },
            {
                'appid': 234567,
                'name': 'Test Game 2',
                'ai_summary': 'Another test game',
                'similarity_score': 0.85
            }
        ],
        'sample_user': {
            'id': 'test_user_id',
            'email': 'test@example.com',
            'display_name': 'Test User'
        }
    } 