"""
Integration tests for search route endpoints.
"""
import pytest
from unittest.mock import patch
import json

@patch('blueprints.search.perform_search')
def test_search_execute_endpoint(mock_perform_search, client):
    """
    Test that the search execute endpoint returns the correct response.
    """
    # Setup mock
    mock_results = [
        {
            'appid': 123456,
            'name': 'Test Game 1',
            'media': ['https://example.com/image.jpg'],
            'genres': ['Action', 'Adventure'],
            'release_year': '2023',
            'platforms': {'windows': True, 'mac': False, 'linux': False},
            'is_free': False,
            'price': 19.99,
            'pos_percent': 66.7,
            'total_reviews': 3,
            'ai_summary': 'A test game about testing'
        }
    ]
    mock_explanation = "Test search explanation"
    mock_perform_search.return_value = (mock_results, mock_explanation)
    
    # Execute
    response = client.post('/search/execute', data={
        'query': 'test query',
        'genre': 'All',
        'year': 'All',
        'platform': 'All',
        'price': 'All',
        'sort_by': 'Relevance',
        'result_limit': '50'
    })
    
    # Assert
    assert response.status_code == 200
    assert b'test query' in response.data
    assert b'Test Game 1' in response.data
    assert mock_perform_search.called
    
    # Check the call arguments
    args, kwargs = mock_perform_search.call_args
    assert args[0] == 'test query'  # First arg is query
    assert kwargs.get('limit') == 50


@patch('blueprints.search.deep_search_status')
def test_deep_search_status_endpoint(mock_status, client):
    """
    Test that the deep search status endpoint returns the correct response.
    """
    # Setup mock
    mock_status.copy.return_value = {
        'active': True,
        'progress': 50,
        'current_step': 'Processing search variations',
        'completed': False,
        'error': None,
        'result_count': 10,
        'ready_for_viewing': False
    }
    
    # Execute
    response = client.get('/deep_search_status')
    
    # Assert
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['active'] is True
    assert data['progress'] == 50
    assert data['current_step'] == 'Processing search variations'
    assert data['completed'] is False
    assert data['result_count'] == 10
    assert data['ready_for_viewing'] is False


@patch('blueprints.search.perform_search')
def test_search_execute_with_filters(mock_perform_search, client):
    """
    Test that search filters are passed correctly to perform_search.
    """
    # Setup mock
    mock_results = []
    mock_explanation = "No results found"
    mock_perform_search.return_value = (mock_results, mock_explanation)
    
    # Execute with filters
    response = client.post('/search/execute', data={
        'query': 'strategy games',
        'genre': 'Strategy',
        'year': '2023',
        'platform': 'Windows',
        'price': 'Free',
        'sort_by': 'Release Date (Newest)',
        'result_limit': '25',
        'use_ai_enhanced': 'on'
    })
    
    # Assert
    assert response.status_code == 200
    
    # Check the call arguments
    args, kwargs = mock_perform_search.call_args
    assert args[0] == 'strategy games'  # First arg is query
    assert args[1] == 'Strategy'  # genre
    assert args[2] == '2023'  # year
    assert args[3] == 'Windows'  # platform
    assert args[4] == 'Free'  # price
    assert args[5] == 'Release Date (Newest)'  # sort_by
    assert kwargs.get('use_ai_enhanced') is True
    assert kwargs.get('limit') == 25 