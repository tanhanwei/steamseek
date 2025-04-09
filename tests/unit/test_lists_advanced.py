"""
Advanced unit tests for lists functionality focusing on edge cases and error handling.
"""
import pytest
from unittest.mock import patch, MagicMock
import json


@patch('flask_login.current_user')
def test_update_list_empty_value(mock_current_user, auth_client):
    """
    Test the update_list API route with an empty value
    """
    # Make the request with empty value
    response = auth_client.post(
        '/api/update_list/list1',
        json={'field': 'name', 'value': ''}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Missing' in data['message'] or 'empty' in data['message'].lower()
    
    # Verify update_list_metadata was not called
    mock_current_user.update_list_metadata.assert_not_called()


@patch('flask_login.current_user')
def test_update_list_missing_field(mock_current_user, auth_client):
    """
    Test the update_list API route with missing field
    """
    # Make the request with missing field
    response = auth_client.post(
        '/api/update_list/list1',
        json={'value': 'New Value'}
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Missing' in data['message']
    
    # Verify update_list_metadata was not called
    mock_current_user.update_list_metadata.assert_not_called()


@patch('flask_login.current_user')
@patch('blueprints.lists.get_game_data_by_appid')
def test_save_game_with_server_error(mock_get_game, mock_current_user, auth_client):
    """
    Test the save_game route when a server error occurs
    """
    # Set up mock to raise exception
    mock_get_game.return_value = {"name": "Test Game", "header_image": "test.jpg", "short_description": "A test game"}
    mock_current_user.add_game_to_list.side_effect = Exception("Database error")
    
    # Make request
    response = auth_client.post(
        '/save_game/123',
        json={'list_ids': ['list1']}
    )
    
    # Verify error handling
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Error' in data['message']


@patch('flask_login.current_user')
def test_remove_game_invalid_appid(mock_current_user, auth_client):
    """
    Test removing a game with an invalid app ID
    """
    # Make the request with non-numeric app ID
    response = auth_client.post('/remove_game/list1/invalid')
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Error' in data['message']
    
    # Verify remove_game_from_list was not called
    mock_current_user.remove_game_from_list.assert_not_called()


@patch('flask_login.current_user')
def test_save_results_as_list_validation(mock_current_user, auth_client):
    """
    Test validation in save_results_as_list endpoint
    """
    # Test with empty name
    response = auth_client.post(
        '/api/save_results_as_list',
        json={'list_name': '', 'results': [{'appid': 123}]}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'name cannot be empty' in data['message'].lower()
    
    # Test with empty results
    response = auth_client.post(
        '/api/save_results_as_list',
        json={'list_name': 'Valid Name', 'results': []}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'no results' in data['message'].lower()


@patch('flask_login.current_user')
def test_save_results_as_list_creation_failure(mock_current_user, auth_client):
    """
    Test save_results_as_list when list creation fails
    """
    # Mock create_list to return None (failure)
    mock_current_user.create_list.return_value = None
    
    # Test data
    results = [
        {
            'appid': 123,
            'name': 'Test Game',
            'media': ['image.jpg'],
            'ai_summary': 'A test game'
        }
    ]
    
    # Make the request
    response = auth_client.post(
        '/api/save_results_as_list',
        json={'list_name': 'Test List', 'results': results}
    )
    
    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Failed to create list' in data['message']
    
    # Verify create_list was called
    mock_current_user.create_list.assert_called_once_with('Test List')
    # Verify add_game_to_list was not called
    mock_current_user.add_game_to_list.assert_not_called()


@patch('flask_login.current_user')
def test_get_game_lists_when_empty(mock_current_user, auth_client):
    """
    Test the get_game_lists API route when user has no lists
    """
    # Mock current_user methods to return empty lists
    mock_current_user.get_game_lists.return_value = []
    mock_current_user.get_lists.return_value = []
    
    # Make the request
    response = auth_client.get('/api/game_lists/123')
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'in_lists' in data
    assert 'all_lists' in data
    assert len(data['in_lists']) == 0
    assert len(data['all_lists']) == 0
    
    # Verify the methods were called correctly
    mock_current_user.get_game_lists.assert_called_once_with('123')
    mock_current_user.get_lists.assert_called_once() 