"""
Integration tests for lists routes with advanced Flask context handling.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from flask import url_for


def test_lists_with_specialized_fixture(list_test_client):
    """
    Test the lists page using the specialized list_test_client fixture
    that properly handles context and common mocks.
    """
    client, mock_current_user = list_test_client
    
    # Make the request
    response = client.get('/lists')
    
    # Verify the response
    assert response.status_code == 200
    assert b'My Favorites' in response.data
    assert b'To Play' in response.data
    
    # Verify get_lists was called
    mock_current_user.get_lists.assert_called_once()


def test_list_detail_with_url_for(list_test_client, app_context):
    """
    Test the list detail page with url_for in Flask context
    """
    client, mock_current_user = list_test_client
    
    # Use url_for in the app_context
    with patch('flask.url_for') as mock_url_for:
        mock_url_for.return_value = '/lists'
        
        # Make the request
        response = client.get('/list/list1')
        
        # Verify the response
        assert response.status_code == 200
        assert b'My Favorites' in response.data
        assert b'Test Game 1' in response.data
        
        # Verify methods were called
        mock_current_user.get_lists.assert_called_once()
        mock_current_user.get_games_in_list.assert_called_once_with('list1')


def test_create_list_sequence(list_test_client):
    """
    Test a sequence of list operations to verify integration
    """
    client, mock_current_user = list_test_client
    
    # 1. Create a new list
    response = client.post('/create_list', data={'list_name': 'New Test List'})
    assert response.status_code == 302
    mock_current_user.create_list.assert_called_once_with('New Test List')
    
    # 2. Check that we can get lists after creating
    mock_current_user.get_lists.return_value.append({
        'id': 'new-list-id', 
        'name': 'New Test List', 
        'description': ''
    })
    
    response = client.get('/lists')
    assert response.status_code == 200
    assert b'New Test List' in response.data
    
    # 3. Add a game to the new list
    mock_get_game = patch('blueprints.lists.get_game_data_by_appid').start()
    mock_get_game.return_value = {
        'name': 'Test Game',
        'header_image': 'test_image.jpg',
        'short_description': 'A test game'
    }
    
    response = client.post(
        '/save_game/123',
        json={'list_ids': ['new-list-id']}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_update_list_metadata_with_content_type(list_test_client):
    """
    Test updating list metadata with explicit content-type header
    """
    client, mock_current_user = list_test_client
    
    # Make the request with explicit content-type
    response = client.post(
        '/api/update_list/list1',
        data=json.dumps({'field': 'name', 'value': 'Updated List Name'}),
        content_type='application/json'
    )
    
    # Verify the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify the method was called correctly
    mock_current_user.update_list_metadata.assert_called_once_with('list1', 'name', 'Updated List Name')


def test_save_results_as_list_integration_sequence(list_test_client):
    """
    Test the full sequence of saving search results as a new list
    """
    client, mock_current_user = list_test_client
    
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
    
    # 1. Save results as a new list
    response = client.post(
        '/api/save_results_as_list',
        json={'list_name': 'Search Results', 'results': results}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['list_id'] == 'new-list-id'
    
    # Verify methods were called
    mock_current_user.create_list.assert_called_once_with('Search Results')
    assert mock_current_user.add_game_to_list.call_count == 2
    
    # 2. Verify the new list appears in user's lists
    mock_current_user.get_lists.return_value.append({
        'id': 'new-list-id', 
        'name': 'Search Results', 
        'description': ''
    })
    
    response = client.get('/lists')
    assert response.status_code == 200
    assert b'Search Results' in response.data 