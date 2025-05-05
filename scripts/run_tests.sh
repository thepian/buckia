#!/bin/bash
# Run tests with coverage report

set -e

# Create directory for scripts
mkdir -p "$(dirname "$0")"

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f .venv/bin/activate ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "Virtual environment not found. Creating one..."
        uv venv .venv
        source .venv/bin/activate
        uv pip install -e ".[bunny,s3,linode,dev]"
    fi
fi

# Default to running all tests
TEST_PATH=${1:-tests/}

# Check for coverage report flag
COVERAGE_FLAG=""
if [ "$2" == "--cov" ] || [ "$2" == "-c" ]; then
    COVERAGE_FLAG="--cov=buckia --cov-report=term --cov-report=html"
fi

# Check if we need to load environment variables
if [ -f .env ]; then
    echo "Found .env file, integration tests will use these credentials if enabled"
fi

# Run the tests
echo "Running tests in $TEST_PATH with uv..."
python -m pytest $TEST_PATH -v $COVERAGE_FLAG $3 $4 $5

# Report success
echo "Tests completed successfully!"

# Open coverage report if generated
if [ -n "$COVERAGE_FLAG" ] && [ -f "htmlcov/index.html" ]; then
    echo "Coverage report generated at htmlcov/index.html"
    if [ "$(uname)" == "Darwin" ]; then
        open htmlcov/index.html
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        xdg-open htmlcov/index.html
    fi
fi