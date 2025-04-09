# SteamSeek Functional Testing Guide

This document outlines the approach, challenges, and solutions for implementing functional tests in the SteamSeek project.

## Functional Testing Overview

Functional tests validate complete user workflows across multiple components. Unlike unit tests that test isolated functions, functional tests simulate real user interactions to ensure different parts of the application work together correctly.

## Test Categories

We've implemented several categories of functional tests:

1. **User Workflow Tests**
   - Authentication flow (login/logout)
   - Search flow (basic search, filtered search, deep search)
   - Lists management flow (create, add/remove games, view)
   - Game interaction flow (view details, analysis, notes)

2. **Cross-Component Tests**
   - Search to game detail to list addition workflow
   - Deep search to organizing games in multiple lists

3. **Performance Tests**
   - Search performance benchmarking
   - Game details rendering performance
   - Lists scaling performance with increasing items

## Challenges and Solutions

During implementation, we encountered several challenges:

### 1. URL Generation Issues

**Challenge**: Flask's template rendering system uses `url_for()` to generate URLs within templates. During testing, this leads to BuildError exceptions because the test environment doesn't have all routes properly registered.

**Solution**: We implemented multiple approaches:
- Direct patching of `flask.render_template` to bypass template rendering entirely
- Creating simplified tests that focus on testing the API interactions rather than rendered HTML
- Using test contexts appropriately to ensure proper URL generation

### 2. Authentication Context

**Challenge**: Testing authenticated routes requires simulating a logged-in user.

**Solution**:
- Using `client.session_transaction()` to manually set session data
- Mocking Flask-Login's `current_user` object
- Creating a specialized `auth_client` fixture that automatically includes authentication

### 3. External Service Dependencies

**Challenge**: The application uses Firebase for authentication and data storage.

**Solution**:
- Comprehensive mocking of Firebase services using unittest.mock
- Creating test-specific data structures that mimic Firebase responses
- Designing tests to validate the correct interaction with these services

## Testing Implementation Approaches

Based on our experimentation, we've identified the following effective approaches:

### Approach 1: Pure API Testing

For routes that return JSON, test only the API interactions without dealing with templates:

```python
@patch('blueprints.search.perform_search')
def test_search_api(self, mock_perform_search, client):
    # Setup mock response
    mock_perform_search.return_value = (mock_results, "Explanation")
    
    # Test API endpoint
    response = client.post('/api/search', json={'query': 'test'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'results' in data
```

### Approach 2: Patched Template Rendering

For routes that render templates, patch the rendering function:

```python
@patch('flask.render_template')
@patch('blueprints.games.get_game_data_by_appid')
def test_game_detail(self, mock_get_game, mock_render, client):
    # Setup mocks
    mock_get_game.return_value = mock_game_data
    mock_render.return_value = "Rendered page"
    
    # Test the view function
    response = client.get('/detail/123456')
    assert response.status_code == 200
    
    # Verify the correct template was rendered with correct data
    mock_render.assert_called_with(
        'detail.html', 
        game=mock_game_data, 
        analysis=ANY, 
        note=ANY
    )
```

### Approach 3: Workflow Testing

For testing full workflows that span multiple endpoints:

```python
def test_auth_workflow(self, mock_db, mock_firebase_auth, client):
    # Setup authentication mocks
    mock_firebase_auth.sign_in_with_email_and_password.return_value = {...}
    
    # 1. Simulate logged-in user
    with client.session_transaction() as session:
        session['user_id'] = "test-user-id"
    
    # 2. Log out
    logout_response = client.get('/logout')
    
    # 3. Verify redirect after logout
    assert logout_response.status_code == 302
    assert '/login' in logout_response.location
```

## Running Functional Tests

To run all functional tests:

```bash
python -m pytest tests/functional/ -v
```

To run specific functional test categories:

```bash
# Run user workflow tests
python -m pytest tests/functional/test_user_workflows.py -v

# Run only authentication tests
python -m pytest tests/functional/test_user_workflows.py::TestAuthenticationWorkflow -v
```

## Recommended Testing Strategy

Based on our experience, we recommend the following approach:

1. Focus on testing API interactions for most functionality
2. Use simplified workflows that bypass template rendering when testing UI interactions
3. For templates, test that the correct template is rendered with the expected context
4. Use integration tests to verify correct database interactions
5. Reserve full end-to-end tests for critical user journeys only

## Conclusion

Functional testing SteamSeek has revealed important insights about the application's architecture and the challenges of testing Flask applications. By focusing on the most critical workflows and using strategic mocking, we've been able to implement effective tests despite the challenges of template rendering and authentication. 