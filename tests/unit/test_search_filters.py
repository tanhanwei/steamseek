"""
Unit tests for search filtering functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from blueprints.search import perform_search


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_with_genre_filter(mock_get_game, mock_semantic_search, app):
    """
    Test that genre filtering works correctly.
    """
    # Setup mock responses
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Action Game', 'ai_summary': 'Action game summary'},
        {'appid': '456', 'name': 'RPG Game', 'ai_summary': 'RPG game summary'}
    ]
    
    # Configure mock to return different games based on appid
    def get_game_side_effect(appid, *args, **kwargs):
        if appid == 123:
            return {
                'appid': 123,
                'name': 'Action Game',
                'header_image': 'https://example.com/action.jpg',
                'release_date': '2022',
                'store_data': {
                    'platforms': {'windows': True, 'mac': False, 'linux': False},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Action'}, {'description': 'Adventure'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            }
        elif appid == 456:
            return {
                'appid': 456,
                'name': 'RPG Game',
                'header_image': 'https://example.com/rpg.jpg',
                'release_date': '2023',
                'store_data': {
                    'platforms': {'windows': True, 'mac': True, 'linux': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}, {'description': 'Strategy'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': False}]
            }
        return None
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Execute search with genre filter for RPG
    with app.app_context():
        results, _ = perform_search('test query', selected_genre='RPG', limit=10)
    
    # Assert only RPG game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 456
    assert results[0]['name'] == 'RPG Game'
    assert 'RPG' in results[0]['genres']
    
    # Execute search with genre filter for Action
    with app.app_context():
        results, _ = perform_search('test query', selected_genre='Action', limit=10)
    
    # Assert only Action game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['name'] == 'Action Game'
    assert 'Action' in results[0]['genres']
    
    # Execute search with genre filter that matches no games
    with app.app_context():
        results, _ = perform_search('test query', selected_genre='Simulation', limit=10)
    
    # Assert no games are returned
    assert len(results) == 0


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_with_year_filter(mock_get_game, mock_semantic_search, app):
    """
    Test that year filtering works correctly.
    """
    # Setup mock responses
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': '2022 Game', 'ai_summary': '2022 game summary'},
        {'appid': '456', 'name': '2023 Game', 'ai_summary': '2023 game summary'}
    ]
    
    # Configure mock to return different games based on appid
    def get_game_side_effect(appid, *args, **kwargs):
        if appid == 123:
            return {
                'appid': 123,
                'name': '2022 Game',
                'release_date': '2022',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Action'}]
                },
                'reviews': [{'voted_up': True}]
            }
        elif appid == 456:
            return {
                'appid': 456,
                'name': '2023 Game',
                'release_date': '2023',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}]
                },
                'reviews': [{'voted_up': True}]
            }
        return None
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Execute search with year filter for 2022
    with app.app_context():
        results, _ = perform_search('test query', selected_year='2022', limit=10)
    
    # Assert only 2022 game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['release_year'] == '2022'
    
    # Execute search with year filter for 2023
    with app.app_context():
        results, _ = perform_search('test query', selected_year='2023', limit=10)
    
    # Assert only 2023 game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 456
    assert results[0]['release_year'] == '2023'
    
    # Execute search with year filter that matches no games
    with app.app_context():
        results, _ = perform_search('test query', selected_year='2024', limit=10)
    
    # Assert no games are returned
    assert len(results) == 0


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_with_platform_filter(mock_get_game, mock_semantic_search, app):
    """
    Test that platform filtering works correctly.
    """
    # Setup mock responses
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Windows Game', 'ai_summary': 'Windows only game'},
        {'appid': '456', 'name': 'Mac Game', 'ai_summary': 'Mac compatible game'}
    ]
    
    # Configure mock to return different games based on appid
    def get_game_side_effect(appid, *args, **kwargs):
        if appid == 123:
            return {
                'appid': 123,
                'name': 'Windows Game',
                'store_data': {
                    'platforms': {'windows': True, 'mac': False, 'linux': False},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Action'}]
                },
                'release_date': '2022',
                'reviews': [{'voted_up': True}]
            }
        elif appid == 456:
            return {
                'appid': 456,
                'name': 'Mac Game',
                'store_data': {
                    'platforms': {'windows': True, 'mac': True, 'linux': False},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}]
                },
                'release_date': '2023',
                'reviews': [{'voted_up': True}]
            }
        return None
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Execute search with platform filter for Windows
    with app.app_context():
        results, _ = perform_search('test query', selected_platform='Windows', limit=10)
    
    # Assert both games are returned (both support Windows)
    assert len(results) == 2
    
    # Execute search with platform filter for Mac
    with app.app_context():
        results, _ = perform_search('test query', selected_platform='Mac', limit=10)
    
    # Assert only Mac game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 456
    assert results[0]['platforms']['mac'] == True
    
    # Execute search with platform filter for Linux
    with app.app_context():
        results, _ = perform_search('test query', selected_platform='Linux', limit=10)
    
    # Assert no games are returned
    assert len(results) == 0


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_with_price_filter(mock_get_game, mock_semantic_search, app):
    """
    Test that price filtering works correctly.
    """
    # Setup mock responses
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Free Game', 'ai_summary': 'Free to play game'},
        {'appid': '456', 'name': 'Paid Game', 'ai_summary': 'Premium game'}
    ]
    
    # Configure mock to return different games based on appid
    def get_game_side_effect(appid, *args, **kwargs):
        if appid == 123:
            return {
                'appid': 123,
                'name': 'Free Game',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': True,
                    'genres': [{'description': 'Action'}]
                },
                'release_date': '2022',
                'reviews': [{'voted_up': True}]
            }
        elif appid == 456:
            return {
                'appid': 456,
                'name': 'Paid Game',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}]
                },
                'release_date': '2023',
                'reviews': [{'voted_up': True}]
            }
        return None
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Execute search with price filter for Free
    with app.app_context():
        results, _ = perform_search('test query', selected_price='Free', limit=10)
    
    # Assert only free game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['is_free'] == True
    
    # Execute search with price filter for Paid
    with app.app_context():
        results, _ = perform_search('test query', selected_price='Paid', limit=10)
    
    # Assert only paid game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 456
    assert results[0]['is_free'] == False


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_with_multiple_filters(mock_get_game, mock_semantic_search, app):
    """
    Test that multiple filters applied together work correctly.
    """
    # Setup mock responses
    mock_semantic_search.return_value = [
        {'appid': '111', 'name': 'Action Free 2022', 'ai_summary': 'Action free 2022 game'},
        {'appid': '222', 'name': 'Action Paid 2022', 'ai_summary': 'Action paid 2022 game'},
        {'appid': '333', 'name': 'RPG Free 2023', 'ai_summary': 'RPG free 2023 game'},
        {'appid': '444', 'name': 'RPG Paid 2023', 'ai_summary': 'RPG paid 2023 game'}
    ]
    
    # Configure mock to return different games based on appid
    def get_game_side_effect(appid, *args, **kwargs):
        games = {
            111: {
                'appid': 111,
                'name': 'Action Free 2022',
                'store_data': {
                    'platforms': {'windows': True, 'mac': False, 'linux': False},
                    'is_free': True,
                    'genres': [{'description': 'Action'}]
                },
                'release_date': '2022',
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            },
            222: {
                'appid': 222,
                'name': 'Action Paid 2022',
                'store_data': {
                    'platforms': {'windows': True, 'mac': False, 'linux': False},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Action'}]
                },
                'release_date': '2022',
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            },
            333: {
                'appid': 333,
                'name': 'RPG Free 2023',
                'store_data': {
                    'platforms': {'windows': True, 'mac': True, 'linux': False},
                    'is_free': True,
                    'genres': [{'description': 'RPG'}]
                },
                'release_date': '2023',
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            },
            444: {
                'appid': 444,
                'name': 'RPG Paid 2023',
                'store_data': {
                    'platforms': {'windows': True, 'mac': True, 'linux': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}]
                },
                'release_date': '2023',
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            }
        }
        return games.get(appid, None)
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Test filtering by genre=RPG, year=2023, price=Free
    with app.app_context():
        results, _ = perform_search('test query', 
                                  selected_genre='RPG', 
                                  selected_year='2023', 
                                  selected_price='Free', 
                                  limit=10)
    
    # Assert only RPG Free 2023 game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 333
    assert results[0]['name'] == 'RPG Free 2023'
    
    # Test filtering by genre=Action, year=2022, price=Paid
    with app.app_context():
        results, _ = perform_search('test query', 
                                  selected_genre='Action', 
                                  selected_year='2022', 
                                  selected_price='Paid', 
                                  limit=10)
    
    # Assert only Action Paid 2022 game is returned
    assert len(results) == 1
    assert results[0]['appid'] == 222
    assert results[0]['name'] == 'Action Paid 2022'
    
    # Test filtering by platform=Linux, year=2023
    with app.app_context():
        results, _ = perform_search('test query', 
                                  selected_platform='Linux', 
                                  selected_year='2023', 
                                  limit=10)
    
    # Assert only RPG Paid 2023 game is returned (only one with Linux support)
    assert len(results) == 1
    assert results[0]['appid'] == 444
    assert results[0]['name'] == 'RPG Paid 2023'
    assert results[0]['platforms']['linux'] == True 