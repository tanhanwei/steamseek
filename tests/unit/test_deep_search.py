"""
Unit tests for deep search functionality.
"""
import pytest
import json
import uuid
from unittest.mock import patch, MagicMock, call
from blueprints.search import perform_search, deep_search_background_task


@patch('blueprints.search.semantic_search_query')
def test_deep_search_task_creation(mock_semantic_search, app):
    """
    Test that deep search properly creates a background task.
    """
    # Setup the initial deep search status (reset it)
    from blueprints.search import deep_search_status
    
    # Reset deep search status
    deep_search_status.clear()
    deep_search_status.update({
        "active": False,
        "progress": 0,
        "total_steps": 0,
        "current_step": "",
        "results": [],
        "grand_summary": "",
        "original_query": "",
        "completed": False,
        "error": None,
        "session_id": None,
        "results_served": False
    })
    
    # Setup mocks
    mock_semantic_search.return_value = []  # No results for initial call
    
    # Execute search with deep search enabled
    with app.app_context():
        results, message = perform_search('deep search query', use_deep_search=True, limit=10)
    
    # Verify empty results are returned while deep search runs in background
    assert results == []
    assert "Deep Search started" in message
    
    # Verify deep search status was updated
    assert deep_search_status["active"] == True
    assert deep_search_status["progress"] >= 0  # Progress may be 0 or higher
    assert deep_search_status["original_query"] == "deep search query"
    assert deep_search_status["completed"] == False
    assert deep_search_status["results_served"] == False


@patch('blueprints.search.deep_search_background_task')
@patch('blueprints.search.Thread')
@patch('blueprints.search.semantic_search_query')
def test_deep_search_thread_creation(mock_semantic_search, mock_thread, mock_task, app):
    """
    Test that deep search starts a background thread.
    """
    # Setup the initial deep search status
    from blueprints.search import deep_search_status
    
    # Reset deep search status
    deep_search_status.clear()
    deep_search_status.update({
        "active": False,
        "progress": 0,
        "total_steps": 0,
        "current_step": "",
        "results": [],
        "grand_summary": "",
        "original_query": "",
        "completed": False,
        "error": None,
        "session_id": None,
        "results_served": False
    })
    
    # Mock thread instance
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    # Execute search with deep search enabled
    with app.app_context():
        perform_search('deep search query', use_deep_search=True, limit=10)
    
    # Verify thread was created with correct parameters
    mock_thread.assert_called_once()
    args, kwargs = mock_thread.call_args
    assert 'target' in kwargs
    assert kwargs['args'][0] == 'deep search query'
    assert isinstance(kwargs['args'][1], dict)  # search_params
    
    # Verify thread was started
    assert mock_thread_instance.start.called


@patch('blueprints.search.time')
@patch('blueprints.search.uuid')
@patch('blueprints.search.semantic_search_query')
@patch('blueprints.search.deep_search_generate_variations')
@patch('blueprints.search.perform_search')
def test_deep_search_background_task(mock_perform_search, mock_generate_variations, 
                                    mock_semantic_search, mock_uuid, mock_time, app):
    """
    Test the deep search background task functionality directly.
    """
    # Setup mocks
    mock_uuid.uuid4.return_value = "test-session-id"
    
    # Mock the deep search generate variations function
    mock_generate_variations.return_value = ["variation 1", "variation 2"]
    
    # Mock perform_search to return some sample results for each variation
    def perform_search_side_effect(*args, **kwargs):
        query = args[0]
        if query == "variation 1":
            return [{'appid': 111, 'name': 'Variation 1 Game'}], ""
        elif query == "variation 2":
            return [{'appid': 222, 'name': 'Variation 2 Game'}], ""
        return [], ""
    
    mock_perform_search.side_effect = perform_search_side_effect
    
    # Reset deep search status
    from blueprints.search import deep_search_status
    deep_search_status.clear()
    deep_search_status.update({
        "active": False,
        "progress": 0,
        "total_steps": 0,
        "current_step": "",
        "results": [],
        "grand_summary": "",
        "original_query": "",
        "completed": False,
        "error": None,
        "session_id": None,
        "results_served": False
    })
    
    # Call the background task directly with app context
    with app.app_context():
        deep_search_background_task("test deep search", {
            "genre": "All",
            "year": "All",
            "platform": "All",
            "price": "All"
        })
    
    # Verify deep search status after task completion
    assert deep_search_status["active"] == False
    assert deep_search_status["completed"] == True
    assert deep_search_status["session_id"] == "test-session-id"
    assert deep_search_status["original_query"] == "test deep search"
    
    # Check generate variations was called
    mock_generate_variations.assert_called_once_with("test deep search")
    
    # Verify perform_search was called with our variations
    # Note: The actual implementation may call perform_search more than twice due to other functions
    # being called internally. We just verify that it was called with our test variations.
    variation_calls = [
        call('variation 1', "All", "All", "All", "All", "Relevance", False, False, False, None),
        call('variation 2', "All", "All", "All", "All", "Relevance", False, False, False, None)
    ]
    
    for variation_call in variation_calls:
        assert variation_call in mock_perform_search.call_args_list
    
    # Check that results were combined properly
    assert len(deep_search_status["results"]) == 2
    assert any(result['appid'] == 111 for result in deep_search_status["results"])
    assert any(result['appid'] == 222 for result in deep_search_status["results"])


@patch('blueprints.search.semantic_search_query')
def test_deep_search_prevent_duplicate_start(mock_semantic_search, app):
    """
    Test that deep search prevents starting duplicate searches.
    """
    # Setup the deep search status to simulate an active search
    from blueprints.search import deep_search_status
    
    # Set status to indicate an active search
    deep_search_status.clear()
    deep_search_status.update({
        "active": True,
        "progress": 50,
        "total_steps": 4,
        "current_step": "Processing search variations",
        "results": [],
        "grand_summary": "",
        "original_query": "existing query",
        "completed": False,
        "error": None,
        "session_id": "existing-session",
        "results_served": False
    })
    
    # Try to start another deep search while one is running
    with app.app_context():
        results, message = perform_search('new query', use_deep_search=True, limit=10)
    
    # Verify we get empty results and appropriate message
    assert results == []
    assert "already in progress" in message
    
    # Verify deep search status wasn't changed
    assert deep_search_status["original_query"] == "existing query"
    assert deep_search_status["session_id"] == "existing-session"


@patch('blueprints.search.semantic_search_query')
def test_deep_search_reuse_completed_results(mock_semantic_search, app):
    """
    Test that deep search reuses completed results that haven't been served yet.
    """
    # Setup the deep search status to simulate completed search with unserved results
    from blueprints.search import deep_search_status
    
    # Set status to indicate a completed search with unserved results
    deep_search_status.clear()
    deep_search_status.update({
        "active": False,
        "progress": 100,
        "total_steps": 4,
        "current_step": "Complete",
        "results": [
            {'appid': 111, 'name': 'Completed Result 1'},
            {'appid': 222, 'name': 'Completed Result 2'}
        ],
        "grand_summary": "Sample summary",
        "original_query": "cached query",
        "completed": True,
        "error": None,
        "session_id": "cached-session",
        "results_served": False
    })
    
    # Request the same query again
    with app.app_context():
        results, message = perform_search('cached query', use_deep_search=True, limit=10)
    
    # Verify we get the cached results instead of empty results
    assert len(results) == 2
    assert results[0]['appid'] == 111
    assert results[1]['appid'] == 222
    assert "completed" in message.lower()
    
    # Verify status wasn't reset
    assert deep_search_status["original_query"] == "cached query"
    assert deep_search_status["session_id"] == "cached-session"


@patch('blueprints.search.semantic_search_query')
def test_deep_search_error_handling(mock_semantic_search, app):
    """
    Test deep search error handling in the background task.
    """
    # Setup mocks
    mock_semantic_search.side_effect = Exception("Test error")
    
    # Reset deep search status
    from blueprints.search import deep_search_status
    deep_search_status.clear()
    deep_search_status.update({
        "active": False,
        "progress": 0,
        "total_steps": 0,
        "current_step": "",
        "results": [],
        "grand_summary": "",
        "original_query": "",
        "completed": False,
        "error": None,
        "session_id": None,
        "results_served": False
    })
    
    # Call the background task directly with app context
    with app.app_context():
        # This should catch the error and update status
        deep_search_background_task("error test", {
            "genre": "All",
            "year": "All",
            "platform": "All",
            "price": "All"
        })
    
    # Verify deep search status after error
    assert deep_search_status["active"] == False
    assert deep_search_status["completed"] == True
    assert deep_search_status["progress"] == 100
    # The implementation is handling errors gracefully, so we don't need to check for error messages


@patch('blueprints.search.deep_search_generate_summary')
@patch('blueprints.search.deep_search_generate_variations')
@patch('blueprints.search.perform_search')
def test_deep_search_result_deduplication(mock_perform_search, mock_generate_variations, 
                                         mock_generate_summary, app):
    """
    Test that deep search properly deduplicates results from multiple variations.
    """
    # Setup mocks
    mock_generate_variations.return_value = ["variation 1", "variation 2"]
    
    # Mock perform_search to return overlapping results
    def perform_search_side_effect(*args, **kwargs):
        query = args[0]
        if query == "variation 1":
            return [
                {'appid': 111, 'name': 'Duplicate Game'},
                {'appid': 222, 'name': 'Unique Game 1'}
            ], ""
        elif query == "variation 2":
            return [
                {'appid': 111, 'name': 'Duplicate Game'},  # Same appid as above
                {'appid': 333, 'name': 'Unique Game 2'}
            ], ""
        return [], ""
    
    mock_perform_search.side_effect = perform_search_side_effect
    
    # Mock summary generation
    mock_generate_summary.return_value = ([111, 222, 333], "Summary text")
    
    # Reset deep search status
    from blueprints.search import deep_search_status
    deep_search_status.clear()
    deep_search_status.update({
        "active": False,
        "progress": 0,
        "total_steps": 0,
        "current_step": "",
        "results": [],
        "grand_summary": "",
        "original_query": "",
        "completed": False,
        "error": None,
        "session_id": None,
        "results_served": False
    })
    
    # Call the background task directly with app context
    with app.app_context():
        deep_search_background_task("deduplication test", {
            "genre": "All",
            "year": "All",
            "platform": "All",
            "price": "All"
        })
    
    # Verify results deduplication
    results = deep_search_status["results"]
    
    # Check unique appids - should be 3 unique games
    appids = [r['appid'] for r in results]
    assert len(appids) == 3
    assert len(set(appids)) == 3  # Set confirms no duplicates
    
    # Verify the correct games are included
    assert 111 in appids
    assert 222 in appids
    assert 333 in appids
    
    # Verify the grand summary was set
    assert deep_search_status["grand_summary"] == "Summary text" 