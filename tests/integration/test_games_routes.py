"""
Integration tests for game-related routes and API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
import json


@patch('blueprints.games.get_game_data_by_appid')
def test_game_detail_page_integration(mock_get_game, client):
    """
    Test the game detail page with integrated components
    """
    # Mock game data
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game',
        'header_image': 'image.jpg',
        'short_description': 'A test game',
        'detailed_description': 'This is a detailed description of the test game.',
        'release_date': '2023-01-01',
        'developers': ['Test Developer'],
        'publishers': ['Test Publisher'],
        'genres': ['Action', 'Adventure'],
        'tags': ['Singleplayer', 'Multiplayer'],
        'price': 19.99
    }
    
    # Mock analysis cache with empty dict to avoid trying to load from a file
    with patch('blueprints.games.analysis_cache', {}):
        # Mock current_user for note retrieval (but keep it anonymous)
        with patch('flask_login.current_user') as mock_current_user:
            mock_current_user.is_authenticated = False
            
            # Make the request
            response = client.get('/detail/123')
            
            # Verify the response
            assert response.status_code == 200
            
            # Check for game name and description
            assert b'Test Game' in response.data
            assert b'A test game' in response.data
            
            # Check for other game details
            assert b'Test Developer' in response.data
            assert b'Test Publisher' in response.data
            assert b'Action' in response.data
            assert b'Adventure' in response.data
            
            # Verify get_game_data_by_appid was called with the right ID
            mock_get_game.assert_called_once()
            call_args = mock_get_game.call_args[0]
            assert call_args[0] == 123


@patch('blueprints.games.generate_game_analysis')
@patch('blueprints.games.get_game_data_by_appid')
def test_analyze_api_integration(mock_get_game, mock_generate, client):
    """
    Test the analyze API endpoint with integrated components
    """
    # Mock game data
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game',
        'short_description': 'A test game'
    }
    
    # Mock analysis data
    mock_generate.return_value = {
        'sentiment': 'Positive',
        'pros': ['Fun gameplay', 'Good graphics'],
        'cons': ['Some bugs', 'Short campaign'],
        'target_audience': 'Casual gamers',
        'similar_games': ['Another Game', 'Yet Another Game'],
        'key_features': ['Open world', 'RPG elements']
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
            
            # Check analysis content
            analysis = data['analysis']
            assert analysis['sentiment'] == 'Positive'
            assert 'Fun gameplay' in analysis['pros']
            assert 'Short campaign' in analysis['cons']
            assert len(analysis['similar_games']) == 2
            assert 'Open world' in analysis['key_features']
            
            # Verify the proper methods were called
            mock_get_game.assert_called_once()
            mock_generate.assert_called_once_with(mock_get_game.return_value)
            mock_save.assert_called_once()


@patch('flask_login.current_user')
def test_game_note_lifecycle(mock_current_user, auth_client):
    """
    Test the full lifecycle of a game note (create, read, update, delete)
    """
    # Set up mock user methods
    mock_current_user.is_authenticated = True
    mock_current_user.get_game_note.return_value = ""  # Initially no note
    mock_current_user.save_game_note.return_value = True
    mock_current_user.delete_game_note.return_value = True
    
    # 1. First, save a new note
    response = auth_client.post(
        '/api/game_note/123',
        json={'note': 'Initial test note.'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    mock_current_user.save_game_note.assert_called_once_with(123, 'Initial test note.')
    
    # 2. Now, mock that the note exists and retrieve it
    mock_current_user.get_game_note.return_value = "Initial test note."
    response = auth_client.get('/api/game_note/123')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['note'] == "Initial test note."
    
    # 3. Update the note
    mock_current_user.save_game_note.reset_mock()  # Reset the mock to clear previous call
    response = auth_client.post(
        '/api/game_note/123',
        json={'note': 'Updated test note.'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    mock_current_user.save_game_note.assert_called_once_with(123, 'Updated test note.')
    
    # 4. Finally, delete the note
    response = auth_client.delete('/api/game_note/123')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    mock_current_user.delete_game_note.assert_called_once_with(123)


@patch('flask_login.current_user')
@patch('blueprints.games.get_game_data_by_appid')
def test_authenticated_game_detail(mock_get_game, mock_current_user, auth_client):
    """
    Test the game detail page with an authenticated user who has a note
    """
    # Mock game data
    mock_get_game.return_value = {
        'appid': 123,
        'name': 'Test Game',
        'header_image': 'image.jpg',
        'short_description': 'A test game'
    }
    
    # Mock user authentication and note
    mock_current_user.is_authenticated = True
    mock_current_user.get_game_note.return_value = "My private note about this game."
    
    # Mock analysis cache
    with patch('blueprints.games.analysis_cache', {}):
        # Make the request
        response = auth_client.get('/detail/123')
        
        # Verify the response
        assert response.status_code == 200
        assert b'Test Game' in response.data
        assert b'My private note about this game.' in response.data
        
        # Verify get_game_note was called with the right ID
        mock_current_user.get_game_note.assert_called_once_with(123)


def test_render_markdown_integration(client):
    """
    Test the markdown rendering API with various markdown inputs
    """
    test_cases = [
        {
            'input': "# Heading\n## Subheading\nText",
            'expected_elements': ['<h1>Heading</h1>', '<h2>Subheading</h2>', 'Text']
        },
        {
            'input': "- List item 1\n- List item 2",
            'expected_elements': ['<li>List item 1</li>', '<li>List item 2</li>']
        },
        {
            'input': "**Bold text**\n*Italic text*",
            'expected_elements': ['<strong>Bold text</strong>', '<em>Italic text</em>']
        },
        {
            'input': "[Link text](http://example.com)",
            'expected_elements': ['<a href="http://example.com">Link text</a>']
        }
    ]
    
    for case in test_cases:
        response = client.post('/api/render_markdown', json={'text': case['input']})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        for expected in case['expected_elements']:
            assert expected in data['html']


def test_unauthenticated_note_access(client):
    """
    Test that unauthenticated users cannot access game notes
    """
    # Test GET request
    response = client.get('/api/game_note/123')
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.headers['Location']
    
    # Test POST request
    response = client.post('/api/game_note/123', json={'note': 'Test note'})
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
    
    # Test DELETE request
    response = client.delete('/api/game_note/123')
    assert response.status_code == 302
    assert '/login' in response.headers['Location'] 