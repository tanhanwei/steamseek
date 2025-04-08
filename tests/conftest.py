"""
Common pytest fixtures for SteamSeek tests.
"""
import os
import sys
import pytest
from flask import Flask

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app after adjusting the path
from app_refactored import app as flask_app

@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    # Configure app for testing
    flask_app.config.update({
        'TESTING': True,
        'DEBUG': True
    })
    
    # Return the app
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    """
    Create a test client for the app.
    """
    return app.test_client()

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