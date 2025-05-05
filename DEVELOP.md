# Buckia Development Guide

This document provides instructions for local development of the Buckia library, including how to set up your development environment, install dependencies, and contribute to the project.

## Development Setup

### Prerequisites

- Python 3.7 or higher
- Git
- pip or [uv](https://github.com/astral-sh/uv) (recommended)

### Installing for Development

To set up Buckia for local development, follow these steps:

1. Clone the repository (if you haven't already):
   ```bash
   git clone https://github.com/yourusername/buckia.git
   cd buckia
   ```

2. Install the package in editable mode with development dependencies:
   
   Using pip:
   ```bash
   pip install -e ".[dev]"
   ```
   
   Using uv:
   ```bash
   uv pip install -e ".[dev]"
   ```

3. Install specific backend dependencies as needed:
   ```bash
   # For Bunny.net backend
   uv pip install -e ".[bunny,dev]"
   
   # For S3 backend
   uv pip install -e ".[s3,dev]"
   
   # For Linode backend
   uv pip install -e ".[linode,dev]"
   
   # For all backends
   uv pip install -e ".[bunny,s3,linode,dev]"
   ```

### Using with uv Virtual Environment

If you're using uv for your development workflow, you can link the local Buckia package to your existing uv environment:

1. Activate your uv environment:
   ```bash
   # If using a standard venv
   source /path/to/your/venv/bin/activate
   
   # If using uv directly
   uv venv activate
   ```

2. Install buckia in development mode:
   ```bash
   cd /path/to/libs/buckia
   uv pip install -e .
   ```

3. Verify the installation:
   ```bash
   # Check if buckia is installed
   uv pip list | grep buckia
   
   # Test importing the package
   python -c "import buckia; print(buckia.__version__)"
   ```

### Using with record_thing Library

To use your local development version of Buckia with the record_thing library:

1. Make sure you're using the same Python environment for both:
   ```bash
   cd /path/to/record_thing
   uv pip install -e /path/to/libs/buckia
   ```

2. Create a test script to verify the integration:
   ```python
   # test_buckia_integration.py
   import buckia
   from record_thing import your_module  # Import your record_thing module
   
   print(f"Buckia version: {buckia.__version__}")
   
   # Test creating a Buckia client
   config = buckia.BucketConfig(
       provider="bunny",
       bucket_name="test-bucket"
   )
   
   client = buckia.BuckiaClient(config)
   print("Successfully initialized Buckia client")
   
   # Add your integration test code here
   ```

3. Run the test script:
   ```bash
   python test_buckia_integration.py
   ```

## Development Workflow

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes to the code.

3. Run tests to ensure your changes don't break existing functionality:
   ```bash
   pytest
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Add your meaningful commit message"
   ```

### Running Tests

To run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=buckia

# Run specific tests
pytest tests/test_specific_module.py
```

### Building Documentation

The documentation is built using Sphinx:

```bash
# Install documentation dependencies
uv pip install -e ".[dev,docs]"

# Build documentation
cd docs
make html
```

## Project Structure

The Buckia package is organized as follows:

```
buckia/
├── __init__.py             # Package initialization
├── client.py               # Main client interface
├── config.py               # Configuration handling
├── cli.py                  # Command-line interface
└── sync/                   # Synchronization backends
    ├── __init__.py
    ├── base.py             # Base sync class
    ├── factory.py          # Backend factory
    ├── bunny.py            # Bunny.net implementation
    ├── s3.py               # S3 implementation
    └── linode.py           # Linode implementation
```

### Adding a New Backend

To add a new storage backend:

1. Create a new file in the `sync` directory (e.g., `sync/mybackend.py`).
2. Implement a class that inherits from `BaseSync`.
3. Implement all required abstract methods.
4. Add the backend to the factory in `sync/factory.py`.
5. Add appropriate dependencies to `setup.py`.

## Troubleshooting

### Common Issues

#### Package Not Found After Installation

If Python can't find the package after installation:

```bash
# Check the installed packages
uv pip list | grep buckia

# Check Python's import path
python -c "import sys; print(sys.path)"
```

#### Changes Not Reflected

If your changes aren't showing up when you import the package:

```bash
# Try restarting the Python interpreter
# If using a notebook, restart the kernel

# Check if you're running the correct Python version
which python
```

#### Import Errors

If you're getting import errors:

```bash
# Verify your dependencies are installed
uv pip install -r requirements.txt

# Check for conflicting packages
uv pip check
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

Please follow the coding style used in the project and include tests for new features. 