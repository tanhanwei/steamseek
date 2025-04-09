"""
Unit tests for games functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os


@patch('blueprints.games.get_game_data_by_appid')
def test_game_detail_valid(mock_get_game, client):
    """
    Test the game detail route with a valid game ID
    """
    # Mock game data
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game',
        'header_image': 'image.jpg',
        'short_description': 'A test game'
    }
    
    # Mock analysis cache with empty dict to avoid trying to load from a file
    with patch('blueprints.games.analysis_cache', {}):
        # Make the request
        response = client.get('/detail/123')
        
        # Verify the response
        assert response.status_code == 200
        assert b'Test Game' in response.data
        
        # Verify get_game_data_by_appid was called with the right ID
        mock_get_game.assert_called_once()
        call_args = mock_get_game.call_args[0]
        assert call_args[0] == 123


@patch('blueprints.games.get_game_data_by_appid')
def test_game_detail_invalid_id(mock_get_game, client):
    """
    Test the game detail route with an invalid game ID
    """
    # Make the request with a non-numeric ID
    response = client.get('/detail/invalid')
    
    # Verify the response
    assert response.status_code == 200  # Renders error template
    assert b'Invalid game ID' in response.data
    
    # Verify get_game_data_by_appid was not called
    mock_get_game.assert_not_called()


@patch('blueprints.games.get_game_data_by_appid')
def test_game_detail_not_found(mock_get_game, client):
    """
    Test the game detail route with a non-existent game ID
    """
    # Mock game data to return None
    mock_get_game.return_value = None
    
    # Make the request
    response = client.get('/detail/999')
    
    # Verify the response
    assert response.status_code == 200  # Renders error template
    assert b'not found' in response.data


@patch('blueprints.games.generate_game_analysis')
@patch('blueprints.games.get_game_data_by_appid')
def test_analyze_game_fresh(mock_get_game, mock_generate, client):
    """
    Test the analyze_game route with a fresh analysis
    """
    # Mock game data
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game'
    }
    
    # Mock analysis data
    mock_generate.return_value = {
        'sentiment': 'Positive',
        'key_features': ['Fun', 'Engaging']
    }
    
    # Mock cache operations
    with patch('blueprints.games.analysis_cache', {}) as mock_cache:
        with patch('blueprints.games.save_analysis_cache') as mock_save:
            # Make the request
            response = client.get('/api/analyze/123')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['source'] == 'fresh'
            assert data['analysis']['sentiment'] == 'Positive'
            
            # Verify mock calls
            mock_get_game.assert_called_once()
            mock_generate.assert_called_once()
            mock_save.assert_called_once()


@patch('blueprints.games.generate_game_analysis')
@patch('blueprints.games.get_game_data_by_appid')
def test_analyze_game_cached(mock_get_game, mock_generate, client):
    """
    Test the analyze_game route with a cached analysis
    """
    # Create a mock cache with pre-existing analysis
    mock_analysis = {
        'appid': 123,
        'sentiment': 'Positive',
        'key_features': ['Fun', 'Engaging']
    }
    
    # Mock cache operations
    with patch('blueprints.games.analysis_cache', {123: mock_analysis}):
        # Make the request
        response = client.get('/api/analyze/123')
        
        # Verify the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['source'] == 'cache'
        assert data['analysis']['sentiment'] == 'Positive'
        
        # Verify game data and generation were not called
        mock_get_game.assert_not_called()
        mock_generate.assert_not_called()


@patch('blueprints.games.generate_game_analysis')
@patch('blueprints.games.get_game_data_by_appid')
def test_analyze_game_force_refresh(mock_get_game, mock_generate, client):
    """
    Test the analyze_game route with forced refresh
    """
    # Mock game data
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game'
    }
    
    # Mock analysis data
    mock_generate.return_value = {
        'sentiment': 'Very Positive',  # Different from cached
        'key_features': ['Fun', 'Engaging', 'New Feature']
    }
    
    # Create a mock cache with pre-existing analysis
    mock_analysis = {
        'appid': 123,
        'sentiment': 'Positive',
        'key_features': ['Fun', 'Engaging']
    }
    
    # Mock cache operations
    with patch('blueprints.games.analysis_cache', {123: mock_analysis}) as mock_cache:
        with patch('blueprints.games.save_analysis_cache') as mock_save:
            # Make the request with refresh parameter
            response = client.get('/api/analyze/123?refresh=true')
            
            # Verify the response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['source'] == 'fresh'
            assert data['analysis']['sentiment'] == 'Very Positive'
            
            # Verify mock calls
            mock_get_game.assert_called_once()
            mock_generate.assert_called_once()
            mock_save.assert_called_once()


@patch('blueprints.games.get_game_data_by_appid')
def test_analyze_game_not_found(mock_get_game, client):
    """
    Test the analyze_game route with a non-existent game
    """
    # Mock game data to return None
    mock_get_game.return_value = None
    
    # Make the request
    response = client.get('/api/analyze/999')
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'not found' in data['message']


def test_load_analysis_cache():
    """
    Test the load_analysis_cache function
    """
    from blueprints.games import load_analysis_cache
    
    # Mock file content with valid and invalid lines
    mock_file_content = (
        '{"appid": 123, "sentiment": "Positive"}\n'
        '{"appid": 456, "sentiment": "Mixed"}\n'
        'invalid json\n'
    )
    
    # Mock open to return our test content
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        with patch('os.path.exists', return_value=True):
            cache = load_analysis_cache('fake_path.jsonl')
            
            # Verify cache loaded correctly
            assert len(cache) == 2
            assert cache[123]['sentiment'] == 'Positive'
            assert cache[456]['sentiment'] == 'Mixed'


def test_save_analysis_cache():
    """
    Test the save_analysis_cache function
    """
    from blueprints.games import save_analysis_cache
    
    # Test data
    cache = {
        123: {'appid': 123, 'sentiment': 'Positive'},
        456: {'appid': 456, 'sentiment': 'Mixed'}
    }
    
    # Mock open
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        save_analysis_cache(cache, 'fake_path.jsonl')
        
        # Verify file was written to
        mock_file.assert_called_once_with('fake_path.jsonl', 'w', encoding='utf-8')
        
        # Verify write calls (one for each cache entry)
        handle = mock_file()
        assert handle.write.call_count == 2


@patch('flask_login.current_user')
def test_game_note_get(mock_current_user, auth_client):
    """
    Test retrieving a game note
    """
    # Mock get_game_note to return a note
    mock_current_user.get_game_note.return_value = "This is my test note."
    
    # Make the request
    response = auth_client.get('/api/game_note/123')
    
    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['note'] == "This is my test note."
    
    # Verify get_game_note was called with the right ID
    mock_current_user.get_game_note.assert_called_once_with(123)


@patch('flask_login.current_user')
def test_game_note_save(mock_current_user, auth_client):
    """
    Test saving a game note
    """
    # Mock save_game_note to return success
    mock_current_user.save_game_note.return_value = True
    
    # Make the request
    response = auth_client.post(
        '/api/game_note/123',
        json={'note': 'This is my test note.'}
    )
    
    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'saved successfully' in data['message']
    
    # Verify save_game_note was called correctly
    mock_current_user.save_game_note.assert_called_once_with(123, 'This is my test note.')


@patch('flask_login.current_user')
def test_game_note_delete(mock_current_user, auth_client):
    """
    Test deleting a game note
    """
    # Mock delete_game_note to return success
    mock_current_user.delete_game_note.return_value = True
    
    # Make the request
    response = auth_client.delete('/api/game_note/123')
    
    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'deleted successfully' in data['message']
    
    # Verify delete_game_note was called correctly
    mock_current_user.delete_game_note.assert_called_once_with(123)


def test_render_markdown(client):
    """
    Test the markdown rendering endpoint
    """
    # Test markdown
    test_markdown = "# Title\n- List item\n- Another item"
    
    # Make the request
    response = client.post(
        '/api/render_markdown',
        json={'text': test_markdown}
    )
    
    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert '<h1>Title</h1>' in data['html']
    assert '<li>List item</li>' in data['html'] 