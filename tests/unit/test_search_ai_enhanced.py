"""
Unit tests for AI-enhanced search functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from blueprints.search import perform_search


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.optimize_search_query')
def test_ai_enhanced_search_basic(mock_optimize, mock_get_game, mock_semantic_search, app):
    """
    Test basic AI-enhanced search functionality.
    """
    # Setup mocks
    mock_optimize.return_value = ("optimized query", "Query was optimized for better results")
    
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Test Game', 'ai_summary': 'Test game summary'}
    ]
    
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game',
        'header_image': 'https://example.com/image.jpg',
        'release_date': '2023',
        'store_data': {
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'is_free': False,
            'price_overview': {'final': 1999},
            'genres': [{'description': 'Action'}]
        },
        'reviews': [{'voted_up': True}, {'voted_up': True}]
    }
    
    # Execute search with AI enhancement enabled
    with app.app_context():
        results, explanation = perform_search('original query', use_ai_enhanced=True, limit=10)
    
    # Verify that optimize_search_query was called
    mock_optimize.assert_called_once_with('original query')
    
    # Verify that semantic_search_query was called with the optimized query
    mock_semantic_search.assert_called_once_with('optimized query', top_k=50)
    
    # Verify results and explanation
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['name'] == 'Test Game'
    assert explanation == "Query was optimized for better results"


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.optimize_search_query')
def test_ai_enhanced_search_with_empty_query(mock_optimize, mock_get_game, mock_semantic_search, app):
    """
    Test AI-enhanced search with empty query.
    """
    # Execute search with empty query
    with app.app_context():
        results, explanation = perform_search('', use_ai_enhanced=True, limit=10)
    
    # Verify that optimize_search_query was not called for empty query
    mock_optimize.assert_not_called()
    
    # Verify that semantic_search_query was called with the empty query
    mock_semantic_search.assert_called_once_with('', top_k=50)


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.optimize_search_query')
def test_ai_enhanced_search_optimization_error(mock_optimize, mock_get_game, mock_semantic_search, app):
    """
    Test AI-enhanced search with error during query optimization.
    """
    # Setup mocks
    mock_optimize.side_effect = Exception("Optimization error")
    
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Test Game', 'ai_summary': 'Test game summary'}
    ]
    
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game',
        'store_data': {
            'platforms': {'windows': True},
            'is_free': False,
            'price_overview': {'final': 1999},
            'genres': [{'description': 'Action'}]
        },
        'release_date': '2023',
        'reviews': [{'voted_up': True}]
    }
    
    # Execute search with AI enhancement enabled
    with app.app_context():
        results, explanation = perform_search('original query', use_ai_enhanced=True, limit=10)
    
    # Verify that optimize_search_query was called but failed
    mock_optimize.assert_called_once_with('original query')
    
    # Verify that semantic_search_query was called with the original query (fallback)
    mock_semantic_search.assert_called_once_with('original query', top_k=50)
    
    # Verify results are still returned despite optimization error
    assert len(results) == 1
    assert results[0]['appid'] == 123
    assert results[0]['name'] == 'Test Game'


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.optimize_search_query')
@patch('blueprints.search.rerank_search_results')
def test_ai_enhanced_search_with_reranking(mock_rerank, mock_optimize, mock_get_game, mock_semantic_search, app):
    """
    Test AI-enhanced search with result reranking.
    """
    # Setup mocks
    mock_optimize.return_value = ("optimized query", "Query was optimized for better results")
    
    # Mock search results with multiple games
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Game A', 'ai_summary': 'Game A summary'},
        {'appid': '456', 'name': 'Game B', 'ai_summary': 'Game B summary'},
        {'appid': '789', 'name': 'Game C', 'ai_summary': 'Game C summary'}
    ]
    
    # Mock game data
    def get_game_side_effect(appid, *args, **kwargs):
        games = {
            123: {
                'appid': 123,
                'name': 'Game A',
                'header_image': 'https://example.com/imageA.jpg',
                'release_date': '2021',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Action'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            },
            456: {
                'appid': 456,
                'name': 'Game B',
                'header_image': 'https://example.com/imageB.jpg',
                'release_date': '2022',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            },
            789: {
                'appid': 789,
                'name': 'Game C',
                'header_image': 'https://example.com/imageC.jpg',
                'release_date': '2023',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': True,
                    'genres': [{'description': 'Strategy'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            }
        }
        return games.get(appid, None)
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Mock reranking to change order to C, A, B
    mock_rerank.return_value = ([789, 123, 456], "Reordered based on relevance")
    
    # Execute search with AI enhancement and sort by relevance
    with app.app_context():
        app.config['index_map'] = {}  # Mock the index_map in app config
        results, explanation = perform_search(
            'original query', 
            use_ai_enhanced=True, 
            sort_by='Relevance',
            limit=10
        )
    
    # Verify that rerank_search_results was called
    assert mock_rerank.called
    
    # Verify results are in the reranked order
    assert len(results) == 3
    assert [r['appid'] for r in results] == [789, 123, 456]
    assert results[0]['name'] == 'Game C'
    assert results[1]['name'] == 'Game A'
    assert results[2]['name'] == 'Game B'


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.optimize_search_query')
@patch('blueprints.search.rerank_search_results')
def test_ai_enhanced_reranking_failure(mock_rerank, mock_optimize, mock_get_game, mock_semantic_search, app):
    """
    Test AI-enhanced search when reranking fails.
    """
    # Setup mocks
    mock_optimize.return_value = ("optimized query", "Query was optimized for better results")
    
    # Mock search results with multiple games
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'Game A', 'ai_summary': 'Game A summary'},
        {'appid': '456', 'name': 'Game B', 'ai_summary': 'Game B summary'}
    ]
    
    # Mock game data
    def get_game_side_effect(appid, *args, **kwargs):
        games = {
            123: {
                'appid': 123,
                'name': 'Game A',
                'release_date': '2021',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Action'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            },
            456: {
                'appid': 456,
                'name': 'Game B',
                'release_date': '2022',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'RPG'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            }
        }
        return games.get(appid, None)
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Mock reranking to fail
    mock_rerank.return_value = (None, "Failed to rerank results")
    
    # Execute search with AI enhancement and sort by relevance
    with app.app_context():
        app.config['index_map'] = {}  # Mock the index_map in app config
        results, explanation = perform_search(
            'original query', 
            use_ai_enhanced=True, 
            sort_by='Relevance',
            limit=10
        )
    
    # Verify that rerank_search_results was called
    assert mock_rerank.called
    
    # Verify results are in the original order (fallback when reranking fails)
    assert len(results) == 2
    assert [r['appid'] for r in results] == [123, 456]
    assert results[0]['name'] == 'Game A'
    assert results[1]['name'] == 'Game B'


@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.get_game_data_by_appid')
@patch('blueprints.search.optimize_search_query')
def test_ai_enhanced_different_sorting(mock_optimize, mock_get_game, mock_semantic_search, app):
    """
    Test AI-enhanced search with different sorting options.
    """
    # Setup mocks
    mock_optimize.return_value = ("optimized query", "Query was optimized for better results")
    
    # Mock search results with multiple games
    mock_semantic_search.return_value = [
        {'appid': '123', 'name': 'A Game', 'ai_summary': 'Game summary'},
        {'appid': '456', 'name': 'B Game', 'ai_summary': 'Game summary'},
        {'appid': '789', 'name': 'C Game', 'ai_summary': 'Game summary'}
    ]
    
    # Mock game data
    def get_game_side_effect(appid, *args, **kwargs):
        games = {
            123: {
                'appid': 123,
                'name': 'A Game',
                'release_date': '2023',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 2999},
                    'genres': [{'description': 'Action'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}, {'voted_up': True}]
            },
            456: {
                'appid': 456,
                'name': 'B Game',
                'release_date': '2021',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 999},
                    'genres': [{'description': 'RPG'}]
                },
                'reviews': [{'voted_up': True}]
            },
            789: {
                'appid': 789,
                'name': 'C Game',
                'release_date': '2022',
                'store_data': {
                    'platforms': {'windows': True},
                    'is_free': False,
                    'price_overview': {'final': 1999},
                    'genres': [{'description': 'Strategy'}]
                },
                'reviews': [{'voted_up': True}, {'voted_up': True}]
            }
        }
        return games.get(appid, None)
    
    mock_get_game.side_effect = get_game_side_effect
    
    # Test Name sorting (A-Z)
    with app.app_context():
        app.config['index_map'] = {}  # Mock the index_map in app config
        results, _ = perform_search(
            'original query', 
            use_ai_enhanced=True, 
            sort_by='Name (A-Z)',
            limit=10
        )
    
    # Verify results are sorted by name
    assert len(results) == 3
    assert [r['name'] for r in results] == ['A Game', 'B Game', 'C Game']
    
    # Test Price sorting (Low to High)
    with app.app_context():
        app.config['index_map'] = {}
        results, _ = perform_search(
            'original query', 
            use_ai_enhanced=True, 
            sort_by='Price (Low to High)',
            limit=10
        )
    
    # Verify results are sorted by price
    assert len(results) == 3
    assert [r['price'] for r in results] == [9.99, 19.99, 29.99]
    
    # Test Release Date sorting (Newest)
    with app.app_context():
        app.config['index_map'] = {}
        results, _ = perform_search(
            'original query', 
            use_ai_enhanced=True, 
            sort_by='Release Date (Newest)',
            limit=10
        )
    
    # Verify results are sorted by release year
    assert len(results) == 3
    assert [r['release_year'] for r in results] == ['2023', '2022', '2021']
    
    # Test Review Count sorting (High to Low)
    with app.app_context():
        app.config['index_map'] = {}
        results, _ = perform_search(
            'original query', 
            use_ai_enhanced=True, 
            sort_by='Review Count (High to Low)',
            limit=10
        )
    
    # Verify results are sorted by review count
    assert len(results) == 3
    assert [r['total_reviews'] for r in results] == [3, 2, 1] 