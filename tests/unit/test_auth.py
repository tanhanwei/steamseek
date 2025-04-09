"""
Unit tests for authentication functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from firebase_config import User


@patch('firebase_config.db')
def test_user_creation(mock_db):
    """
    Test User class initialization
    """
    # Create a User instance
    user = User(uid="test123", email="test@example.com", display_name="Test User", photo_url="https://example.com/photo.jpg")
    
    # Verify attributes are set correctly
    assert user.id == "test123"
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.photo_url == "https://example.com/photo.jpg"


@patch('firebase_config.db')
def test_user_get_method(mock_db):
    """
    Test User.get static method
    """
    # Mock the document get method and its return value
    mock_document = MagicMock()
    mock_document.exists = True
    mock_document.to_dict.return_value = {
        'email': 'test@example.com',
        'display_name': 'Test User',
        'photo_url': 'https://example.com/photo.jpg'
    }
    
    # Mock the Firestore chain of calls
    mock_collection = MagicMock()
    mock_document_ref = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document_ref
    mock_document_ref.get.return_value = mock_document
    
    # Call the method
    user = User.get("test123")
    
    # Verify the correct Firestore methods were called
    mock_db.collection.assert_called_once_with('users')
    mock_collection.document.assert_called_once_with('test123')
    mock_document_ref.get.assert_called_once()
    
    # Verify the user was created with the correct attributes
    assert user.id == "test123"
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.photo_url == "https://example.com/photo.jpg"


@patch('firebase_config.db')
def test_user_get_method_nonexistent_user(mock_db):
    """
    Test User.get static method when user doesn't exist
    """
    # Mock the document get method and its return value
    mock_document = MagicMock()
    mock_document.exists = False
    
    # Mock the Firestore chain of calls
    mock_collection = MagicMock()
    mock_document_ref = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document_ref
    mock_document_ref.get.return_value = mock_document
    
    # Call the method
    user = User.get("nonexistent123")
    
    # Verify None is returned for nonexistent user
    assert user is None


@patch('firebase_config.db')
def test_user_create_or_update(mock_db):
    """
    Test User.create_or_update method
    """
    # Create a User instance
    user = User(uid="test123", email="test@example.com", display_name="Test User", photo_url="https://example.com/photo.jpg")
    
    # Mock the Firestore chain of calls
    mock_collection = MagicMock()
    mock_document_ref = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document_ref
    
    # Call the method
    result = user.create_or_update()
    
    # Verify the correct Firestore methods were called
    mock_db.collection.assert_called_once_with('users')
    mock_collection.document.assert_called_once_with('test123')
    
    # Verify set was called with the correct data
    mock_document_ref.set.assert_called_once()
    call_args = mock_document_ref.set.call_args[0][0]
    assert call_args['email'] == "test@example.com"
    assert call_args['display_name'] == "Test User"
    assert call_args['photo_url'] == "https://example.com/photo.jpg"
    assert 'last_login' in call_args
    
    # Verify merge=True was passed
    assert mock_document_ref.set.call_args[1]['merge'] is True
    
    # Verify the method returned True on success
    assert result is True


@patch('firebase_config.db')
def test_user_create_or_update_error(mock_db):
    """
    Test User.create_or_update method when an error occurs
    """
    # Create a User instance
    user = User(uid="test123", email="test@example.com")
    
    # Make the Firestore set method raise an exception
    mock_collection = MagicMock()
    mock_document_ref = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document_ref
    mock_document_ref.set.side_effect = Exception("Firestore error")
    
    # Call the method
    result = user.create_or_update()
    
    # Verify the method returned False on error
    assert result is False


def test_auth_google_route(client):
    """
    Test the auth_google route
    """
    # Mock UUID and os.environ
    with patch('blueprints.auth.uuid') as mock_uuid:
        with patch('blueprints.auth.os') as mock_os:
            # Configure mocks
            mock_uuid.uuid4.return_value = "test-state-value"
            mock_os.environ.get.return_value = "test-client-id"
            
            # Make the request
            response = client.get('/auth/google')
            
            # Verify the response is a redirect
            assert response.status_code == 302
            
            # Verify the redirect URL contains the correct parameters
            location = response.headers['Location']
            assert "accounts.google.com/o/oauth2/v2/auth" in location
            assert "client_id=test-client-id" in location
            assert "state=test-state-value" in location
            assert "redirect_uri=http://localhost:5000/auth/google/callback" in location


def test_auth_callback_success(client):
    """
    Test the successful auth_callback flow
    """
    # Set up session state
    with client.session_transaction() as sess:
        sess['oauth_state'] = 'test-state-value'
    
    # Mock all required components
    with patch('blueprints.auth.requests.post') as mock_post:
        # Mock token response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id_token': 'fake-token',
            'access_token': 'fake-access-token'
        }
        mock_post.return_value = mock_response
        
        # Mock Firebase auth
        with patch('blueprints.auth.firebase_auth') as mock_firebase_auth:
            mock_firebase_auth.sign_in_with_custom_token.return_value = {
                'idToken': {
                    'localId': 'test123',
                    'email': 'test@example.com',
                    'displayName': 'Test User',
                    'photoUrl': 'https://example.com/photo.jpg'
                }
            }
            
            # Mock User class
            with patch('blueprints.auth.User') as mock_user_class:
                mock_user = MagicMock()
                mock_user.create_or_update.return_value = True
                mock_user_class.return_value = mock_user
                
                # Mock login_user
                with patch('blueprints.auth.login_user') as mock_login_user:
                    
                    # Make the request
                    response = client.get('/auth/google/callback?state=test-state-value&code=test-auth-code')
                    
                    # Verify redirect
                    assert response.status_code == 302
                    assert 'search' in response.headers['Location']
                    
                    # Verify user was created
                    mock_user_class.assert_called_once()
                    
                    # Verify login_user was called
                    mock_login_user.assert_called_once()


def test_auth_callback_invalid_state(client):
    """
    Test auth_callback with invalid state
    """
    # Set up session state
    with client.session_transaction() as sess:
        sess['oauth_state'] = 'correct-state-value'
    
    # Make the request with incorrect state
    response = client.get('/auth/google/callback?state=invalid-state-value')
    
    # Verify redirect to login
    assert response.status_code == 302
    assert 'login' in response.headers['Location']


def test_auth_callback_error_param(client):
    """
    Test auth_callback with error parameter
    """
    # Set up session state
    with client.session_transaction() as sess:
        sess['oauth_state'] = 'test-state-value'
    
    # Make the request with error parameter
    response = client.get('/auth/google/callback?state=test-state-value&error=access_denied')
    
    # Verify redirect to login
    assert response.status_code == 302
    assert 'login' in response.headers['Location']


def test_auth_callback_no_code(client):
    """
    Test auth_callback with no code parameter
    """
    # Set up session state
    with client.session_transaction() as sess:
        sess['oauth_state'] = 'test-state-value'
    
    # Make the request without code parameter
    response = client.get('/auth/google/callback?state=test-state-value')
    
    # Verify redirect to login
    assert response.status_code == 302
    assert 'login' in response.headers['Location'] 