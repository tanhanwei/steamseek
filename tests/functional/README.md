# SteamSeek Functional Tests

This directory contains functional tests for SteamSeek. These tests verify complete user workflows and cross-component interactions, simulating real user behavior.

## Test Categories

The functional tests are organized into several categories:

1. **User Workflows** (`test_user_workflows.py`): Tests for individual component workflows:
   - Authentication flow (register, login, logout)
   - Search flow (basic search, filtered search, deep search)
   - Lists management flow (create, add/remove games, delete)
   - Game interaction flow (view details, analysis, notes)

2. **Cross-Component Workflows** (`test_cross_component_workflows.py`): Tests that span multiple components:
   - Search to game detail to list workflow
   - Deep search to multiple lists workflow

3. **Performance Tests** (`test_performance.py`): Tests that measure performance:
   - Search response times
   - Game details rendering times
   - Lists scaling performance
   - Authentication response times

## Running the Tests

### Run all functional tests:

```bash
pytest tests/functional/
```

### Run specific workflow tests:

```bash
# Run authentication workflow tests
pytest tests/functional/test_user_workflows.py::TestAuthenticationWorkflow

# Run search workflow tests
pytest tests/functional/test_user_workflows.py::TestSearchWorkflow

# Run list management tests
pytest tests/functional/test_user_workflows.py::TestListsWorkflow

# Run game interaction tests
pytest tests/functional/test_user_workflows.py::TestGameInteractionWorkflow
```

### Run cross-component tests:

```bash
pytest tests/functional/test_cross_component_workflows.py
```

### Run performance tests:

```bash
pytest tests/functional/test_performance.py
```

## Test Setup and Mocking

The functional tests use extensive mocking to simulate server responses and external services:

- Flask test client and authenticated client from the main test fixtures
- Mocked Firebase authentication and database operations
- Mocked search engine responses
- Mocked game data and analysis

## Adding New Functional Tests

When adding new functional tests:

1. Consider which category the test belongs to
2. Ensure the test simulates a real user workflow or interaction
3. Use appropriate mocking for external services and data
4. Follow the pattern of other tests for consistent style

## Performance Test Thresholds

The performance tests include thresholds that represent acceptable response times:

- Search operations: < 0.5s average
- Game details: < 0.3s average
- List operations:
  - 10 items: < 0.2s
  - 50 items: < 0.4s
  - 100 items: < 0.8s
- Authentication: < 0.3s average

These thresholds may need adjustment based on your development environment and application complexity. 