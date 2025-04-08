"""
Unit tests for search functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from blueprints.search import perform_search


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_perform_search_basic(mock_get_game, mock_semantic_search, app):
    """
    Test basic search functionality with mocked search results.
    """
    # Setup
    mock_semantic_search.return_value = [
        {
            'appid': '123456',
            'name': 'Test Game 1',
            'ai_summary': 'A test game about testing',
            'similarity_score': 0.95
        }
    ]
    
    # Mock game data return
    mock_game_data = {
        'appid': 123456,
        'name': 'Test Game 1',
        'short_description': 'A game for testing',
        'header_image': 'https://example.com/image.jpg',
        'release_date': '2023',
        'store_data': {
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'is_free': False,
            'price_overview': {'final': 1999},
            'genres': [{'description': 'Action'}, {'description': 'Adventure'}]
        },
        'reviews': [
            {'voted_up': True, 'review': 'Great game!'},
            {'voted_up': True, 'review': 'Awesome!'},
            {'voted_up': False, 'review': 'Not my style.'}
        ]
    }
    mock_get_game.return_value = mock_game_data
    
    # Execute
    with app.app_context():
        results, explanation = perform_search('test query', limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0]['appid'] == 123456
    assert results[0]['name'] == 'Test Game 1'
    assert mock_semantic_search.called
    assert mock_get_game.called


@patch('blueprints.search.semantic_search_query')
def test_perform_search_no_results(mock_semantic_search, app):
    """
    Test search with no results.
    """
    # Setup
    mock_semantic_search.return_value = []
    
    # Execute
    with app.app_context():
        results, explanation = perform_search('no results query', limit=10)
    
    # Assert
    assert len(results) == 0
    assert mock_semantic_search.called


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_perform_search_with_filters(mock_get_game, mock_semantic_search, app):
    """
    Test search with filters applied.
    """
    # Setup
    mock_semantic_search.return_value = [
        {
            'appid': '123456',
            'name': 'Test Game 1',
            'ai_summary': 'A test game about testing',
            'similarity_score': 0.95
        },
        {
            'appid': '234567',
            'name': 'Test Game 2',
            'ai_summary': 'Another test game',
            'similarity_score': 0.85
        }
    ]
    
    # Mock game data returns
    game1 = {
        'appid': 123456,
        'name': 'Test Game 1',
        'short_description': 'A game for testing',
        'header_image': 'https://example.com/image.jpg',
        'release_date': '2023',
        'store_data': {
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'is_free': False,
            'price_overview': {'final': 1999},
            'genres': [{'description': 'Action'}, {'description': 'Adventure'}]
        },
        'reviews': [{'voted_up': True}, {'voted_up': True}, {'voted_up': False}]
    }
    
    game2 = {
        'appid': 234567,
        'name': 'Test Game 2',
        'short_description': 'Another game for testing',
        'header_image': 'https://example.com/image2.jpg',
        'release_date': '2022',
        'store_data': {
            'platforms': {'windows': True, 'mac': True, 'linux': False},
            'is_free': True,
            'genres': [{'description': 'Strategy'}, {'description': 'Simulation'}]
        },
        'reviews': [{'voted_up': True}, {'voted_up': True}]
    }
    
    # Configure mock to return different games based on appid
    def get_game_side_effect(appid, *args, **kwargs):
        if appid == 123456:
            return game1
        elif appid == 234567:
            return game2
        return None
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Execute search with genre filter - should only return game2 (Strategy)
    with app.app_context():
        results, _ = perform_search('test query', selected_genre='Strategy', limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0]['appid'] == 234567
    assert results[0]['name'] == 'Test Game 2'
    
    # Execute search with price filter - should only return game2 (Free)
    with app.app_context():
        results, _ = perform_search('test query', selected_price='Free', limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0]['appid'] == 234567
    assert results[0]['name'] == 'Test Game 2'
    
    # Execute search with platform filter - should only return game2 (mac)
    with app.app_context():
        results, _ = perform_search('test query', selected_platform='Mac', limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0]['appid'] == 234567
    assert results[0]['name'] == 'Test Game 2'
    
    # Execute search with year filter - should only return game1 (2023)
    with app.app_context():
        results, _ = perform_search('test query', selected_year='2023', limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0]['appid'] == 123456
    assert results[0]['name'] == 'Test Game 1' 