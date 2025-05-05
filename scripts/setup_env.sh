#!/bin/bash
# Setup development environment

set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source .venv/bin/activate

# Install package in development mode with all dependencies
echo "Installing package with dependencies..."
uv pip install -e ".[bunny,s3,linode,dev]"

# Create .env file if it doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env with your API keys for testing."
fi

echo ""
echo "Environment setup complete!"
echo "Activate the virtual environment with: source .venv/bin/activate"
echo "Run tests with: ./scripts/run_tests.sh"
echo ""