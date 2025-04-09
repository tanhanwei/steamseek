"""
Integration tests for authentication routes.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import session


@patch('blueprints.auth.uuid')
def test_login_page_renders(mock_uuid, client):
    """
    Test that the login page renders correctly
    """
    # Make the request
    response = client.get('/login')
    
    # Verify response
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Sign in with Google' in response.data


@patch('blueprints.auth.current_user')
def test_login_redirects_if_authenticated(mock_current_user, client):
    """
    Test that login route redirects to search page if user is already authenticated
    """
    # Mock authenticated user
    mock_current_user.is_authenticated = True
    
    # Make the request
    response = client.get('/login')
    
    # Verify the response is a redirect to search page
    assert response.status_code == 302
    assert response.headers['Location'] == '/search'


@patch('blueprints.auth.uuid')
def test_login_post_redirects_to_google_auth(mock_uuid, client):
    """
    Test that POST to /login redirects to Google auth
    """
    # Make the request
    response = client.post('/login')
    
    # Verify the response is a redirect to Google auth
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/google'


@patch('blueprints.auth.firebase_auth')
@patch('blueprints.auth.login_user')
@patch('blueprints.auth.request')
def test_auth_callback_route_integration(mock_request, mock_login_user, mock_firebase_auth, client):
    """
    Integration test for auth_callback route
    """
    # Mock request.args
    mock_request.args.get.side_effect = lambda key, *args: {
        'state': 'test-state-value',
        'code': 'test-auth-code',
    }.get(key)
    
    mock_request.args.__contains__.return_value = False  # 'error' not in request.args
    
    # Mock the successful token response
    with patch('blueprints.auth.requests.post') as mock_post:
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {
            'id_token': 'fake-id-token',
            'access_token': 'fake-access-token'
        }
        mock_post.return_value = mock_token_response
        
        # Mock Firebase sign in
        mock_firebase_auth.sign_in_with_custom_token.return_value = {
            'idToken': {
                'localId': 'test123',
                'email': 'test@example.com',
                'displayName': 'Test User',
                'photoUrl': 'https://example.com/photo.jpg'
            }
        }
        
        # Mock User creation
        with patch('blueprints.auth.User') as mock_user_class:
            mock_user = MagicMock()
            mock_user.create_or_update.return_value = True
            mock_user_class.return_value = mock_user
            
            # Set up session state
            with client.session_transaction() as sess:
                sess['oauth_state'] = 'test-state-value'
            
            # Make the request
            response = client.get('/auth/google/callback?state=test-state-value&code=test-auth-code')
            
            # Verify the response
            assert response.status_code == 302
            assert response.headers['Location'] == '/search'
            
            # Verify login_user was called
            mock_login_user.assert_called_once_with(mock_user)


@patch('blueprints.auth.login_required')
@patch('blueprints.auth.logout_user')
def test_logout_route_integration(mock_logout_user, mock_login_required, client):
    """
    Integration test for logout route
    """
    # Mock login_required to avoid authentication check
    mock_login_required.return_value = lambda f: f
    
    # Make the request
    response = client.get('/logout')
    
    # Verify the response is a redirect
    assert response.status_code == 302
    assert response.headers['Location'] == '/search'
    
    # Verify logout_user was called
    mock_logout_user.assert_called_once()


def test_protected_route_redirects_unauthenticated(client):
    """
    Test that protected routes redirect unauthenticated users to login
    """
    # Create a protected route for testing
    from flask import Blueprint, request, session, redirect, url_for
    from flask_login import login_required
    
    # Configure test Flask application
    from flask import Flask
    from flask_login import LoginManager
    
    test_bp = Blueprint('test', __name__)
    
    @test_bp.route('/protected')
    @login_required
    def protected_route():
        return "Protected content"
    
    # Register the blueprint with the app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-key'
    app.config['TESTING'] = True
    app.register_blueprint(test_bp)
    
    # Set up LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Create test client
    with app.test_client() as test_client:
        # Make the request to protected route
        response = test_client.get('/protected')
        
        # Verify redirect to login page
        assert response.status_code == 302
        assert '/login' in response.headers['Location'] 