#!/bin/bash
# Publish Buckia to PyPI using API token
#
# Usage:
#   1. Get PyPI API token from https://pypi.org/manage/account/token/
#   2. Add to .env file: PYPI_API_TOKEN=pypi-your_token_here
#   3. Run: ./scripts/publish.sh

set -e

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a  # stop automatically exporting
fi

# Check if token is set
if [ -z "$PYPI_API_TOKEN" ]; then
    echo "❌ Error: PYPI_API_TOKEN not set in .env file"
    echo ""
    echo "To fix this:"
    echo "1. Get a PyPI API token from https://pypi.org/manage/account/token/"
    echo "2. Add to .env file: PYPI_API_TOKEN=pypi-your_token_here"
    exit 1
fi

echo "🔨 Building package..."
uv build

echo "📦 Publishing to PyPI..."
TWINE_USERNAME=__token__ TWINE_PASSWORD=$PYPI_API_TOKEN uv run twine upload dist/*

echo "✅ Published successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Tag the version: git tag v$(python -c 'import buckia; print(buckia.__version__)')"
echo "2. Push the tag: git push origin v$(python -c 'import buckia; print(buckia.__version__)')"
