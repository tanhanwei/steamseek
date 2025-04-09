"""
Integration tests for lists routes.
"""
import pytest
from unittest.mock import patch, MagicMock
import json


@patch('flask_login.current_user')
def test_lists_page_load(mock_current_user, auth_client):
    """
    Test that the lists page loads correctly for an authenticated user
    """
    # Mock current user lists
    mock_current_user.get_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games'},
        {'id': 'list2', 'name': 'To Play', 'description': 'Games I want to play'}
    ]
    
    # Make the request
    response = auth_client.get('/lists')
    
    # Verify response
    assert response.status_code == 200
    assert b'My Favorites' in response.data
    assert b'To Play' in response.data
    
    # Verify get_lists was called
    mock_current_user.get_lists.assert_called_once()


@patch('flask_login.current_user')
def test_list_detail_page_load(mock_current_user, auth_client):
    """
    Test that the list detail page loads correctly
    """
    # Mock current user lists
    mock_current_user.get_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games'}
    ]
    
    # Mock games in list
    mock_current_user.get_games_in_list.return_value = [
        {'appid': 123, 'name': 'Test Game 1', 'header_image': 'image1.jpg'},
        {'appid': 456, 'name': 'Test Game 2', 'header_image': 'image2.jpg'}
    ]
    
    # Make the request
    response = auth_client.get('/list/list1')
    
    # Verify response
    assert response.status_code == 200
    assert b'My Favorites' in response.data
    assert b'Test Game 1' in response.data
    assert b'Test Game 2' in response.data
    
    # Verify methods were called
    mock_current_user.get_lists.assert_called_once()
    mock_current_user.get_games_in_list.assert_called_once_with('list1')


@patch('flask_login.current_user')
def test_create_list_integration(mock_current_user, auth_client):
    """
    Test creating a new list
    """
    # Mock create_list to return a list ID
    mock_current_user.create_list.return_value = 'new-list-id'
    
    # Make the request
    response = auth_client.post('/create_list', data={'list_name': 'New Test List'})
    
    # Verify redirect
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists'
    
    # Verify create_list was called
    mock_current_user.create_list.assert_called_once_with('New Test List')


@patch('flask_login.current_user')
def test_api_game_lists(mock_current_user, auth_client):
    """
    Test the API endpoint for getting game lists
    """
    # Mock the user methods
    mock_current_user.get_game_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites'}
    ]
    mock_current_user.get_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites'},
        {'id': 'list2', 'name': 'To Play'}
    ]
    
    # Make the request
    response = auth_client.get('/api/game_lists/123')
    
    # Verify response
    assert response.status_code == 200
    
    # Parse JSON response
    data = json.loads(response.data)
    assert 'in_lists' in data
    assert 'all_lists' in data
    assert len(data['in_lists']) == 1
    assert len(data['all_lists']) == 2
    
    # Verify methods were called
    mock_current_user.get_game_lists.assert_called_once_with('123')
    mock_current_user.get_lists.assert_called_once()


@patch('flask_login.current_user')
@patch('blueprints.lists.get_game_data_by_appid')
def test_save_game_to_list(mock_get_game, mock_current_user, auth_client):
    """
    Test saving a game to a list
    """
    # Mock game data
    mock_get_game.return_value = {
        'name': 'Test Game',
        'header_image': 'test_image.jpg',
        'short_description': 'A test game'
    }
    
    # Mock add_game_to_list
    mock_current_user.add_game_to_list.return_value = True
    
    # Make the request
    response = auth_client.post(
        '/save_game/123',
        json={'list_ids': ['list1']}
    )
    
    # Verify response
    assert response.status_code == 200
    
    # Parse JSON response
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify methods were called
    mock_get_game.assert_called_once()
    mock_current_user.add_game_to_list.assert_called_once()


@patch('flask_login.current_user')
def test_remove_game_from_list(mock_current_user, auth_client):
    """
    Test removing a game from a list
    """
    # Mock remove_game_from_list
    mock_current_user.remove_game_from_list.return_value = True
    
    # Make the request
    response = auth_client.post('/remove_game/list1/123')
    
    # Verify response
    assert response.status_code == 200
    
    # Parse JSON response
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'removed' in data['message']
    
    # Verify methods were called
    mock_current_user.remove_game_from_list.assert_called_once_with('list1', 123)


@patch('flask_login.current_user')
def test_update_list_metadata_integration(mock_current_user, auth_client):
    """
    Test updating list metadata
    """
    # Mock update_list_metadata
    mock_current_user.update_list_metadata.return_value = True
    
    # Make the request
    response = auth_client.post(
        '/api/update_list/list1',
        json={'field': 'name', 'value': 'Updated List Name'}
    )
    
    # Verify response
    assert response.status_code == 200
    
    # Parse JSON response
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'updated successfully' in data['message']
    
    # Verify methods were called
    mock_current_user.update_list_metadata.assert_called_once_with('list1', 'name', 'Updated List Name')


@patch('flask_login.current_user')
def test_save_results_as_list_integration(mock_current_user, auth_client):
    """
    Test saving search results as a new list
    """
    # Mock create_list
    mock_current_user.create_list.return_value = 'new-list-id'
    
    # Mock add_game_to_list
    mock_current_user.add_game_to_list.return_value = True
    
    # Test data
    results = [
        {
            'appid': 123,
            'name': 'Test Game 1',
            'media': ['image1.jpg'],
            'ai_summary': 'A test game about testing'
        },
        {
            'appid': 456,
            'name': 'Test Game 2',
            'media': ['image2.jpg'],
            'ai_summary': 'Another test game'
        }
    ]
    
    # Make the request
    response = auth_client.post(
        '/api/save_results_as_list',
        json={'list_name': 'Search Results', 'results': results}
    )
    
    # Verify response
    assert response.status_code == 200
    
    # Parse JSON response
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'Created list' in data['message']
    assert data['list_id'] == 'new-list-id'
    
    # Verify methods were called
    mock_current_user.create_list.assert_called_once_with('Search Results')
    assert mock_current_user.add_game_to_list.call_count == 2


def test_unauthenticated_access(client):
    """
    Test that unauthenticated users are redirected to login
    """
    # List of protected routes to test
    protected_routes = [
        '/lists',
        '/list/list1',
        '/api/game_lists/123',
    ]
    
    # Test POST endpoints
    post_routes = [
        '/create_list',
        '/save_game/123',
        '/remove_game/list1/123',
        '/api/update_list/list1',
        '/api/save_results_as_list'
    ]
    
    # Check GET routes
    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 302  # Redirects to login
        assert '/login' in response.headers['Location']
    
    # Check POST routes
    for route in post_routes:
        response = client.post(route, json={})
        assert response.status_code == 302  # Redirects to login
        assert '/login' in response.headers['Location'] 