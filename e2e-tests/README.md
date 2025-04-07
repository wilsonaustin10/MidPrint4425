# MidPrint End-to-End Tests

This directory contains end-to-end tests for the MidPrint application, testing the integration between the frontend and backend components.

## Directory Structure

```
e2e-tests/
├── conftest.py           # Common test fixtures and utilities
├── requirements.txt      # Test-specific dependencies
├── run_tests.py         # Test runner script
├── test_nav_01.py       # Navigation tests
├── test_form_01.py      # Form interaction tests
├── test_flow_01.py      # Multi-step workflow tests
├── templates/           # Test template files
├── test_reports/        # Generated test reports
└── results/            # Test artifacts (screenshots, logs, etc.)
```

## Setup

1. Install test dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure backend dependencies are installed:
   ```bash
   cd ../backend
   pip install -r requirements.txt
   ```

## Running Tests

### Using the Test Runner

The test runner script provides a comprehensive way to run all tests and generate reports:

```bash
python run_tests.py
```

This will:
- Start the backend server if not running
- Execute all test modules
- Generate a test report in test_reports/
- Display a summary of results

### Using pytest Directly

You can also run tests using pytest for more control:

```bash
# Run all tests
pytest

# Run specific test file
pytest test_nav_01.py

# Run tests in parallel
pytest -n auto

# Generate HTML report
pytest --html=report.html

# Run with increased verbosity
pytest -v
```

## Test Categories

1. Navigation Tests (`test_nav_01.py`)
   - Basic URL navigation
   - Page state verification
   - Screenshot capture

2. Form Interaction Tests (`test_form_01.py`)
   - Form field input
   - Form submission
   - Validation handling

3. Multi-step Workflow Tests (`test_flow_01.py`)
   - Complex user interactions
   - State management
   - Error handling

## Writing New Tests

1. Create a new test file following the naming convention: `test_*_*.py`
2. Import necessary fixtures from `conftest.py`
3. Use the provided `api_client` fixture for making requests
4. Add test module to `TEST_MODULES` in `run_tests.py`
5. Update test categorization in `TEST_CATEGORIES`

Example:
```python
import pytest
from pathlib import Path

async def test_example(api_client, browser_manager):
    # Test implementation
    response = await api_client.post("/api/v1/agent/execute", json={
        "description": "Navigate to example.com"
    })
    assert response.status_code == 200
```

## Test Reports

Test reports are generated in two formats:
1. JSON reports in `test_reports/` directory
2. Console summary with test results and metrics

The reports include:
- Test execution time
- Screenshot counts
- Action feedback messages
- Errors and failures
- Category-wise results

## Debugging Failed Tests

1. Check the test logs in `results/`
2. Review screenshots in `results/screenshots/`
3. Examine the backend logs
4. Use pytest's `-v` flag for verbose output
5. Use pytest's `--pdb` flag to debug failures

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Add appropriate documentation
3. Include test data in `templates/` if needed
4. Update this README if adding new test categories 