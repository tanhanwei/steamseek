# SteamSeek Testing

This directory contains tests for the SteamSeek application. The tests are organized into three categories:

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test interactions between components
3. **Functional Tests**: Test complete user workflows

## Setup

Install pytest and related packages:

```bash
pip install pytest pytest-flask pytest-cov
```

## Running Tests

### Run all tests:

```bash
pytest
```

### Run specific test types:

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only functional tests
pytest tests/functional/
```

### Run with coverage:

```bash
# Run tests with coverage report
pytest --cov=blueprints

# Run with detailed coverage report
pytest --cov=blueprints --cov-report=html
```

The HTML coverage report will be generated in the `htmlcov` directory.

### Run a specific test file:

```bash
pytest tests/unit/test_search.py
```

### Run a specific test:

```bash
pytest tests/unit/test_search.py::test_perform_search_basic
```

## Test Configuration

Test configuration is defined in `conftest.py`. This file contains fixtures that set up the test environment, including:

- Flask app configuration for testing
- Test client
- Mock data

## Mocking

The tests use `unittest.mock` for mocking:

- External API calls
- Database access
- Complex dependencies

Example of mocking:

```python
@patch('blueprints.search.semantic_search_query')
def test_example(mock_semantic_search):
    mock_semantic_search.return_value = [{'mock': 'data'}]
    # Test code here
```

## Conventions

1. Test files are named `test_*.py`
2. Test functions are named `test_*`
3. Each test file should import only the modules it needs to test
4. Tests should be independent and not rely on other tests
5. Tests should clean up after themselves

## Adding New Tests

When adding new tests:

1. Identify the appropriate test type (unit, integration, functional)
2. Create or update the test file in the appropriate directory
3. Follow the existing test patterns
4. Ensure the tests are well-documented
5. Update the `TESTING_ROADMAP.md` with your progress 