"""
Unit tests for search error handling.
"""
import pytest
from unittest.mock import patch, MagicMock
from blueprints.search import perform_search


@patch('blueprints.search.semantic_search_query')
def test_search_with_empty_query(mock_semantic_search, app):
    """
    Test search with empty query.
    """
    # Execute
    with app.app_context():
        results, explanation = perform_search('', limit=10)
    
    # Assert
    assert len(results) == 0
    assert mock_semantic_search.called
    mock_semantic_search.assert_called_once_with('', top_k=50)


@patch('blueprints.search.semantic_search_query')
def test_search_with_very_long_query(mock_semantic_search, app):
    """
    Test search with an excessively long query.
    """
    # Setup a very long query of 1000 characters
    long_query = "a" * 1000
    
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Test Game', 'ai_summary': 'Test game summary'}
    ]
    
    # Execute
    with app.app_context():
        results, explanation = perform_search(long_query, limit=10)
    
    # Assert that the query was processed
    assert mock_semantic_search.called
    # The query should be passed as-is to semantic_search_query
    mock_semantic_search.assert_called_once_with(long_query, top_k=50)


@patch('blueprints.search.semantic_search_query')
def test_search_with_special_characters(mock_semantic_search, app):
    """
    Test search with special characters in the query.
    """
    # Setup a query with special characters
    special_query = "game!@#$%^&*()_+{}|:<>?~"
    
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Test Game', 'ai_summary': 'Test game summary'}
    ]
    
    # Execute
    with app.app_context():
        results, explanation = perform_search(special_query, limit=10)
    
    # Assert that the query was processed correctly
    assert mock_semantic_search.called
    mock_semantic_search.assert_called_once_with(special_query, top_k=50)


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_with_invalid_appid(mock_get_game, mock_semantic_search, app):
    """
    Test handling of invalid appid in search results.
    """
    # Setup mock to return an appid that isn't in the database
    mock_semantic_search.return_value = [
        {'appid': '999', 'name': 'Nonexistent Game', 'ai_summary': 'Summary'}
    ]
    
    # Mock get_game_data_by_appid to return None for this appid
    mock_get_game.return_value = None
    
    # Execute
    with app.app_context():
        results, explanation = perform_search('test query', limit=10)
    
    # Assert that results are empty since the game data couldn't be retrieved
    assert len(results) == 0
    assert mock_get_game.called


@patch('blueprints.search.semantic_search_query')
def test_search_semantic_search_error(mock_semantic_search, app):
    """
    Test handling of error in semantic search.
    """
    # Setup mock to raise an exception
    mock_semantic_search.side_effect = Exception("Semantic search error")
    
    # Execute
    with app.app_context():
        results, explanation = perform_search('test query', limit=10)
    
    # Assert empty results are returned when there's an error
    assert len(results) == 0
    assert mock_semantic_search.called


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_missing_game_data_fields(mock_get_game, mock_semantic_search, app):
    """
    Test handling of missing fields in game data.
    """
    # Setup
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Test Game', 'ai_summary': 'Test game summary'}
    ]
    
    # Mock game data with missing fields
    incomplete_game_data = {
        'appid': 123,
        'name': 'Test Game',
        # Missing header_image, release_date, store_data, reviews
    }
    
    mock_get_game.return_value = incomplete_game_data
    
    # Execute
    with app.app_context():
        results, explanation = perform_search('test query', limit=10)
    
    # Assert the result is still returned with default values for missing fields
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['name'] == 'Test Game'
    assert results[0]['genres'] == []  # Default empty list for missing fields
    assert results[0]['is_free'] == False  # Default value for missing is_free


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
def test_search_invalid_price_data(mock_get_game, mock_semantic_search, app):
    """
    Test handling of invalid price data.
    """
    # Setup
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Test Game', 'ai_summary': 'Test game summary'}
    ]
    
    # Mock game data with invalid price format
    game_with_invalid_price = {
        'appid': 123,
        'name': 'Test Game',
        'header_image': 'https://example.com/image.jpg',
        'release_date': '2023',
        'store_data': {
            'platforms': {'windows': True},
            'is_free': False,
            'price_overview': {'final': 'not-a-number'},  # Invalid price value
            'genres': [{'description': 'Action'}]
        },
        'reviews': [{'voted_up': True}]
    }
    
    mock_get_game.return_value = game_with_invalid_price
    
    # Execute
    with app.app_context():
        results, explanation = perform_search('test query', limit=10)
    
    # Assert the result is still returned with a default price value
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['name'] == 'Test Game'
    assert results[0]['price'] == 0.0  # Default price when parsing fails


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.rerank_search_results')
def test_search_reranking_error(mock_rerank, mock_get_game, mock_semantic_search, app):
    """
    Test handling of error during result reranking.
    """
    # Setup
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Game A', 'ai_summary': 'Summary A'},
        {'appid': '456', 'name': 'Game B', 'ai_summary': 'Summary B'}
    ]
    
    # Mock game data
    def get_game_side_effect(appid, *args, **kwargs):
        if appid == 123:
            return {
                'appid': 123,
                'name': 'Game A',
                'release_date': '2023',
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
                'name': 'Game B',
                'release_date': '2022',
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
    
    # Setup reranking to raise an exception
    mock_rerank.side_effect = Exception("Reranking error")
    
    # Execute search with sort by relevance (which triggers reranking)
    with app.app_context():
        app.config['index_map'] = {}  # Mock the index_map in app config
        results, explanation = perform_search('test query', sort_by='Relevance', limit=10)
    
    # Assert that results are still returned in original order despite reranking error
    assert len(results) == 2
    assert results[0]['appid'] == 123
    assert results[1]['appid'] == 456
    assert mock_rerank.called 