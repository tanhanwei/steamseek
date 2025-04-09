"""
Unit tests for lists functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from flask import url_for


@patch('flask_login.current_user')
def test_user_lists_route(mock_current_user, auth_client):
    """
    Test the user_lists route
    """
    # Set up mock for current_user.get_lists
    mock_current_user.get_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games'},
        {'id': 'list2', 'name': 'To Play', 'description': 'Games I want to play'}
    ]
    
    # Make the request
    response = auth_client.get('/lists')
    
    # Verify the response
    assert response.status_code == 200
    assert b'My Favorites' in response.data
    assert b'To Play' in response.data
    
    # Verify get_lists was called
    mock_current_user.get_lists.assert_called_once()


@patch('flask_login.current_user')
def test_view_list_route(mock_current_user, auth_client):
    """
    Test the view_list route
    """
    # Mock user_lists
    mock_current_user.get_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites', 'description': 'My favorite games'}
    ]
    
    # Mock games in list
    mock_current_user.get_games_in_list.return_value = [
        {'appid': 123, 'name': 'Game 1', 'header_image': 'image1.jpg'},
        {'appid': 456, 'name': 'Game 2', 'header_image': 'image2.jpg'}
    ]
    
    # Make the request
    response = auth_client.get('/list/list1')
    
    # Verify the response
    assert response.status_code == 200
    assert b'My Favorites' in response.data
    assert b'Game 1' in response.data
    assert b'Game 2' in response.data
    
    # Verify methods were called
    mock_current_user.get_lists.assert_called_once()
    mock_current_user.get_games_in_list.assert_called_once_with('list1')


@patch('flask_login.current_user')
def test_view_list_not_found(mock_current_user, auth_client):
    """
    Test the view_list route with a non-existent list
    """
    # Mock empty user_lists
    mock_current_user.get_lists.return_value = []
    
    # Make the request
    response = auth_client.get('/list/nonexistent')
    
    # Verify the redirect
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists'


@patch('flask_login.current_user')
def test_create_list_route(mock_current_user, auth_client):
    """
    Test the create_list route
    """
    # Mock create_list method
    mock_current_user.create_list.return_value = 'new-list-id'
    
    # Make the request
    response = auth_client.post('/create_list', data={'list_name': 'My New List'})
    
    # Verify the redirect
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists'
    
    # Verify create_list was called with the right name
    mock_current_user.create_list.assert_called_once_with('My New List')


@patch('flask_login.current_user')
def test_create_list_empty_name(mock_current_user, auth_client):
    """
    Test the create_list route with an empty list name
    """
    # Make the request with empty name
    response = auth_client.post('/create_list', data={'list_name': ''})
    
    # Verify the redirect
    assert response.status_code == 302
    assert response.headers['Location'] == '/lists'
    
    # Verify create_list was not called
    mock_current_user.create_list.assert_not_called()


@patch('flask_login.current_user')
def test_get_game_lists_route(mock_current_user, auth_client):
    """
    Test the get_game_lists API route
    """
    # Mock current_user methods
    mock_current_user.get_game_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites'}
    ]
    mock_current_user.get_lists.return_value = [
        {'id': 'list1', 'name': 'My Favorites'},
        {'id': 'list2', 'name': 'To Play'}
    ]
    
    # Make the request
    response = auth_client.get('/api/game_lists/123')
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'in_lists' in data
    assert 'all_lists' in data
    assert len(data['in_lists']) == 1
    assert len(data['all_lists']) == 2
    assert data['in_lists'][0]['id'] == 'list1'
    
    # Verify the methods were called correctly
    mock_current_user.get_game_lists.assert_called_once_with('123')
    mock_current_user.get_lists.assert_called_once()


@patch('flask_login.current_user')
@patch('blueprints.lists.get_game_data_by_appid')
def test_save_game_route(mock_get_game, mock_current_user, auth_client):
    """
    Test the save_game route
    """
    # Mock the game data
    mock_get_game.return_value = {
        'name': 'Test Game',
        'header_image': 'test_image.jpg',
        'short_description': 'A test game'
    }
    
    # Mock successful game add
    mock_current_user.add_game_to_list.return_value = True
    
    # Make the request
    response = auth_client.post(
        '/save_game/123',
        json={'list_ids': ['list1', 'list2']}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'saved successfully' in data['message']
    
    # Verify add_game_to_list was called for each list
    assert mock_current_user.add_game_to_list.call_count == 2
    

@patch('flask_login.current_user')
@patch('blueprints.lists.get_game_data_by_appid')
def test_save_game_no_lists(mock_get_game, mock_current_user, auth_client):
    """
    Test the save_game route with no selected lists
    """
    # Make the request with empty list_ids
    response = auth_client.post(
        '/save_game/123',
        json={'list_ids': []}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'No lists selected' in data['message']
    
    # Verify get_game_data_by_appid was not called
    mock_get_game.assert_not_called()


@patch('flask_login.current_user')
@patch('blueprints.lists.get_game_data_by_appid')
def test_save_game_not_found(mock_get_game, mock_current_user, auth_client):
    """
    Test the save_game route with a non-existent game
    """
    # Mock the game data as None (not found)
    mock_get_game.return_value = None
    
    # Make the request
    response = auth_client.post(
        '/save_game/999',
        json={'list_ids': ['list1']}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'not found' in data['message']
    
    # Verify get_game_data_by_appid was called
    mock_get_game.assert_called_once()
    
    # Verify add_game_to_list was not called
    mock_current_user.add_game_to_list.assert_not_called()


@patch('flask_login.current_user')
def test_remove_game_route(mock_current_user, auth_client):
    """
    Test the remove_game route
    """
    # Mock successful game removal
    mock_current_user.remove_game_from_list.return_value = True
    
    # Make the request
    response = auth_client.post('/remove_game/list1/123')
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'removed' in data['message']
    
    # Verify remove_game_from_list was called correctly
    mock_current_user.remove_game_from_list.assert_called_once_with('list1', 123)


@patch('flask_login.current_user')
def test_remove_game_failure(mock_current_user, auth_client):
    """
    Test the remove_game route when removal fails
    """
    # Mock failed game removal
    mock_current_user.remove_game_from_list.return_value = False
    
    # Make the request
    response = auth_client.post('/remove_game/list1/123')
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Failed' in data['message']


@patch('flask_login.current_user')
def test_update_list_metadata(mock_current_user, auth_client):
    """
    Test the update_list API route
    """
    # Mock successful update
    mock_current_user.update_list_metadata.return_value = True
    
    # Make the request
    response = auth_client.post(
        '/api/update_list/list1',
        json={'field': 'name', 'value': 'New List Name'}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'updated successfully' in data['message']
    
    # Verify update_list_metadata was called correctly
    mock_current_user.update_list_metadata.assert_called_once_with('list1', 'name', 'New List Name')


@patch('flask_login.current_user')
def test_update_list_invalid_field(mock_current_user, auth_client):
    """
    Test the update_list API route with an invalid field
    """
    # Make the request with invalid field
    response = auth_client.post(
        '/api/update_list/list1',
        json={'field': 'invalid_field', 'value': 'New Value'}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Invalid field' in data['message']
    
    # Verify update_list_metadata was not called
    mock_current_user.update_list_metadata.assert_not_called()


@patch('flask_login.current_user')
def test_save_results_as_list(mock_current_user, auth_client):
    """
    Test the save_results_as_list API route
    """
    # Mock the create_list method
    mock_current_user.create_list.return_value = 'new-list-id'
    
    # Mock the add_game_to_list method
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
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'Created list' in data['message']
    assert data['list_id'] == 'new-list-id'
    
    # Verify create_list was called
    mock_current_user.create_list.assert_called_once_with('Search Results')
    
    # Verify add_game_to_list was called for each game
    assert mock_current_user.add_game_to_list.call_count == 2 