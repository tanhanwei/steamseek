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
| Search | `test_search.py` | 🔄 Partial | High |
| Authentication | `test_auth.py` | 🔄 Partial | High |
| Lists | `test_lists.py` | ❌ Not Started | Medium |
| Games | `test_games.py` | ❌ Not Started | Medium |
| Data Loader | `test_data_loader.py` | ❌ Not Started | Medium |
| LLM Processor | `test_llm_processor.py` | ❌ Not Started | Medium |

### Integration Tests
| Component | Files | Status | Priority |
|-----------|-------|--------|----------|
| Search Routes | `test_search_routes.py` | 🔄 Partial | High |
| Auth Routes | `test_auth_routes.py` | 🔄 Partial | High |
| Lists Routes | `test_lists_routes.py` | ❌ Not Started | Medium |
| Games Routes | `test_games_routes.py` | ❌ Not Started | Medium |
| Firebase Integration | `test_firebase.py` | ❌ Not Started | Medium |

### Functional Tests
| User Flow | Files | Status | Priority |
|-----------|-------|--------|----------|
| Search & Filter | `test_search_flow.py` | ❌ Not Started | High |
| Login & Account | `test_login_flow.py` | ❌ Not Started | High |
| List Management | `test_list_flow.py` | ❌ Not Started | Medium |
| Game Details & Notes | `test_game_flow.py` | ❌ Not Started | Medium |

## Critical Test Cases

### Search Functionality
- [ ] Basic search returns relevant results
- [ ] AI-enhanced search optimizes queries correctly
- [ ] Deep search generates appropriate variations
- [ ] Filters (genre, year, platform, price) work correctly
- [ ] Sort options change result order appropriately
- [ ] Empty search queries are handled gracefully
- [ ] Special characters in search queries work correctly
- [ ] Very long search queries don't cause issues

### Authentication
- [ ] Login with Google works correctly
- [ ] Logout works correctly
- [ ] Protected routes require authentication
- [ ] User session persistence works correctly
- [ ] Invalid authentication attempts are handled gracefully

### Lists and Notes
- [ ] Creating a new list works correctly
- [ ] Adding games to lists works correctly
- [ ] Removing games from lists works correctly
- [ ] List metadata updates (name, description) work correctly
- [ ] Game notes are saved and retrieved correctly
- [ ] Markdown rendering in notes works correctly

### Game Details
- [ ] Game details page loads correctly
- [ ] Game analysis is generated/cached correctly
- [ ] Media (screenshots, videos) display correctly
- [ ] Game information is displayed correctly

## Testing Milestones

### Milestone 1: Core Search Testing
- Basic unit tests for search functionality
- Integration tests for search endpoints
- Test for filters and sorting options

### Milestone 2: Authentication Testing
- Unit tests for authentication utilities
- Integration tests for auth endpoints
- Test protected routes work correctly

### Milestone 3: Lists and Notes Testing
- Unit tests for list and note operations
- Integration tests for list and note endpoints
- Test for data persistence

### Milestone 4: Game Details Testing
- Unit tests for game data retrieval
- Integration tests for game detail endpoints
- Test for analysis generation and caching

### Milestone 5: Full User Flow Testing
- Functional tests for complete user workflows
- Performance testing under concurrent users
- Error case testing

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

---

*Last Updated: [Date]* 