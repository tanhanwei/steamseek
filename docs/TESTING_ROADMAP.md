# SteamSeek Testing Roadmap

This document tracks the testing strategy, current coverage, and future testing priorities for the SteamSeek project.

## Testing Strategy

SteamSeek uses a combination of test types:

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test interactions between components (e.g., blueprints, database)
3. **Functional Tests**: Test complete user workflows

## Current Test Coverage

### Unit Tests
| Component | Files | Status | Priority |
|-----------|-------|--------|----------|
| Search | `test_search.py`, `test_search_filters.py`, `test_search_ai_enhanced.py`, `test_deep_search.py`, `test_search_errors.py` | ✅ Complete | High |
| Authentication | `test_auth.py`, `test_user_lists.py` | ✅ Complete | High |
| Lists | `test_lists.py`, `test_lists_advanced.py` | ✅ Complete | Medium |
| Games | `test_games.py` | ✅ Complete | Medium |
| Data Loader | `test_data_loader.py` | ✅ Complete | Medium |
| LLM Processor | `test_llm_processor.py` | ❌ Not Started | Medium |

### Integration Tests
| Component | Files | Status | Priority |
|-----------|-------|--------|----------|
| Search Routes | `test_search_routes.py` | 🔄 Partial | High |
| Auth Routes | `test_auth_routes.py` | 🔄 Partial | High |
| Lists Routes | `test_lists_routes.py`, `test_lists_context.py` | ✅ Complete | Medium |
| Games Routes | `test_games_routes.py` | ✅ Complete | Medium |
| Firebase Integration | `test_firebase.py` | ❌ Not Started | Medium |

### Functional Tests
| User Flow | Files | Status | Priority |
|-----------|-------|--------|----------|
| Authentication | `simplified_test.py`, `test_user_workflows.py` | ✅ Complete | High |
| Search | `simplified_test.py`, `test_user_workflows.py` | 🔄 Partial | High |
| Lists | `simplified_test.py`, `test_user_workflows.py` | 🔄 Partial | Medium |
| Cross-Component | `simplified_test.py`, `test_cross_component_workflows.py` | 🔄 Partial | Medium |
| Performance | `test_performance.py` | 🔄 Partial | Medium |

## Critical Test Cases

### Search Functionality
- [x] Basic search returns relevant results
- [x] AI-enhanced search optimizes queries correctly
- [x] Deep search generates appropriate variations
- [x] Filters (genre, year, platform, price) work correctly
- [x] Sort options change result order appropriately
- [x] Empty search queries are handled gracefully
- [x] Special characters in search queries work correctly
- [x] Very long search queries don't cause issues

### Authentication
- [x] User object initialization works correctly
- [x] User retrieval from database works
- [x] User creation/update in database works
- [x] Login with Google flow works correctly
- [x] Auth callback handling works correctly
- [x] Error handling for auth works properly
- [x] Protected routes require authentication
- [x] User session persistence works correctly

### Lists and Notes
- [x] User can create a new list
- [x] User can retrieve lists
- [x] User can add games to lists
- [x] User can remove games from lists
- [x] User can check if a game is in a list
- [x] User can save and retrieve game notes
- [x] User can delete game notes
- [x] List metadata updates (name, description) work correctly
- [x] Markdown rendering in notes works correctly
- [x] Error handling for list operations works properly
- [x] Edge cases (empty lists, validation) are handled correctly

### Game Details
- [x] Game details page loads correctly
- [x] Game analysis is generated/cached correctly
- [x] Game information is displayed correctly
- [x] Game notes can be added, retrieved, and deleted
- [x] Media content is handled correctly
- [x] Analysis cache works properly
- [x] Error handling for invalid game IDs works properly

### Data Loader
- [x] Index building works correctly
- [x] Index caching operates as expected
- [x] Game data retrieval by appid works correctly
- [x] Summary loading functions correctly
- [x] Error handling for missing or corrupt data works properly
- [x] File operations are handled safely

### Functional Workflows
- [x] Complete authentication flow (login/logout)
- [🔄] Complete search flow (basic search, filtering, deep search)
- [🔄] Complete lists management flow (create, add/remove games, delete)
- [🔄] Complete game interaction flow (view details, analysis, notes)
- [🔄] Cross-component workflow from search to game detail to list
- [🔄] Cross-component workflow from deep search to multiple lists
- [🔄] Performance benchmarks for search operations
- [🔄] Performance benchmarks for game details rendering
- [🔄] Performance benchmarks for list operations with scaling
- [x] Performance benchmarks for authentication operations

## Testing Milestones

### Milestone 1: Core Search Testing ✅
- ✅ Basic unit tests for search functionality
- ✅ Unit tests for search filters and sorting options
- ✅ Unit tests for AI-enhanced search
- ✅ Unit tests for deep search background tasks
- ✅ Unit tests for search error handling
- ✅ Integration tests for search endpoints

### Milestone 2: Authentication Testing ✅
- ✅ Unit tests for User class initialization and methods
- ✅ Unit tests for User list and note management
- ✅ Unit tests for auth routes and callbacks
- ✅ Integration tests for auth endpoints
- ✅ Test protected routes work correctly

### Milestone 3: Lists and Notes Testing ✅
- ✅ Unit tests for User list and note operations
- ✅ Unit tests for list API endpoints
- ✅ Integration tests for list and note endpoints
- ✅ Advanced tests for error handling and edge cases
- ✅ Tests for context handling and complete list operations

### Milestone 4: Game Details Testing ✅
- ✅ Unit tests for game data retrieval
- ✅ Unit tests for game details and analysis
- ✅ Unit tests for game notes functionality
- ✅ Integration tests for game detail endpoints
- ✅ Tests for analysis generation and caching

### Milestone 5: Data Management Testing ✅
- ✅ Unit tests for data loader index building
- ✅ Unit tests for game data retrieval
- ✅ Unit tests for summaries loading
- ✅ Integration tests for data loading workflow
- ✅ Tests for error handling in data operations

### Milestone 6: Full User Flow Testing 🔄
- ✅ Functional test structure design and implementation
- ✅ Authentication workflows (login/logout)
- 🔄 Search workflows (facing template rendering challenges)
- 🔄 Lists management workflows (facing template rendering challenges)
- 🔄 Game interaction workflows (facing template rendering challenges)
- 🔄 Cross-component workflows (facing template rendering challenges)
- ✅ Documentation for functional testing approaches
- ❌ Stress testing under concurrent users
- ❌ Security testing

## Mocking Strategy

For tests that require external services:
- Firebase Authentication: Use mock auth service
- Firebase Firestore: Use mock database
- OpenRouter API: Use mock API responses
- Game data: Use small test dataset

## Test Execution

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/functional/

# Run specific functional test categories
pytest tests/functional/test_user_workflows.py
pytest tests/functional/test_cross_component_workflows.py
pytest tests/functional/test_performance.py

# Run with coverage report
pytest --cov=blueprints tests/
```

## Test Environment Setup

```python
# Use this fixture for Flask app context
@pytest.fixture
def app():
    app = create_app(config=TestConfig)
    with app.app_context():
        yield app

# Use this fixture for authenticated client
@pytest.fixture
def auth_client(app):
    with app.test_client() as client:
        # Setup mock authentication
        mock_login(client)
        yield client
```

## Testing Challenges

### Flask Context Issues
When testing Flask route handlers, especially those requiring authentication, we've encountered challenges with:
- Mocking the current_user object correctly
- Patching route decorators like @login_required
- Ensuring the correct Flask request context is available
- Getting JSON responses from routes due to mock serialization issues

These issues can be addressed by:
- Using the auth_client fixture for authenticated routes
- Implementing proper request context handling
- Creating specialized test endpoints that bypass certain checks in test mode
- Using integration tests instead of unit tests for complex route handlers
- Using the specialized list_test_client fixture for list operations

### Template Rendering Issues
When implementing functional tests, we encountered challenges with Flask's template rendering:
- URL generation using url_for() causes BuildError exceptions in tests
- Jinja2 template errors occur when rendering templates with mock data
- Difficulty testing the complete user experience due to template issues

Our solutions for functional testing include:
- Patching flask.render_template to bypass template rendering
- Focusing on testing the API interactions rather than the rendered HTML
- Creating simplified functional tests that validate workflows without templates
- Documenting effective approaches in the FUNCTIONAL_TESTING.md guide

## Recent Test Implementations

### Functional Tests (2023-10-25)
- **Core Test Structure**: Created functional test framework in test_user_workflows.py and test_cross_component_workflows.py
- **Authentication Tests**: Successfully implemented and validated login/logout workflows
- **Template Rendering Solutions**: Developed approach to bypass template rendering issues in tests
- **Documentation**: Created FUNCTIONAL_TESTING.md with detailed guidance on functional testing approaches
- **Simplified Tests**: Created simplified_test.py with focused workflow tests that avoid template rendering issues

### Lists Advanced Tests (2023-10-20)
- **Edge Case Tests**: Added tests for empty values, missing fields, and error conditions
- **Error Handling Tests**: Tests for server errors, invalid input, and API edge cases
- **Context Handling**: Added tests with proper Flask context handling to resolve context issues
- **Integration Sequences**: Added tests for complete list operation sequences

### Games Module Tests (2023-10-20)
- **Game Detail Tests**: Testing for game detail page, invalid IDs, and not found cases
- **Analysis Tests**: Testing for analysis generation, caching, and forced refresh
- **Game Notes Tests**: Testing for note creation, retrieval, and deletion
- **Integration Tests**: Full lifecycle tests for game notes and analysis operations

### Data Loader Tests (2023-10-20)
- **Index Building Tests**: Tests for creating and caching game data indices
- **Data Retrieval Tests**: Tests for fetching game data by app ID
- **Summaries Tests**: Tests for loading game summaries
- **Error Handling**: Tests for file not found, invalid data, and other errors
- **Integration Tests**: Complete data loading workflow tests

---

*Last Updated: 2023-10-25* 