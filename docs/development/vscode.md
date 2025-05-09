# VSCode Setup for Buckia Development

This guide will help you set up Visual Studio Code to work effectively with the Buckia codebase, especially handling relative imports correctly.

## Recommended Extensions

Make sure you have these VS Code extensions installed:

- **Python** (`ms-python.python`) - Core Python language support
- **Pylance** (`ms-python.vscode-pylance`) - Fast, feature-rich language server
- **Black Formatter** (`ms-python.black-formatter`) - Code formatting
- **Ruff** (`charliermarsh.ruff`) - Fast Python linter
- **Python Docstring Generator** (`njpwerner.autodocstring`) - Generates docstrings
- **Mypy Type Checker** (`ms-python.mypy-type-checker`) - Type checking
- **Even Better TOML** (`tamasfe.even-better-toml`) - TOML file support

The project's `.vscode/extensions.json` file should prompt you to install these automatically.

## Workspace Setup

For the best experience, open the project using the workspace file:

1. In VS Code, choose **File → Open Workspace from File...**
2. Select `buckia.code-workspace` from the project root

This workspace file includes the necessary settings to correctly handle relative imports in the Buckia package.

## Configuration Files

The project includes several configuration files to ensure correct linting, type checking, and import resolution:

- `.vscode/settings.json` - Editor settings and Python configuration
- `pyrightconfig.json` - Pylance/Pyright settings for type checking
- `pytest.ini` - Test configuration
- `pyproject.toml` - Project metadata and tool configuration

## Troubleshooting Relative Imports

If Pylance still shows errors with relative imports:

1. Make sure you've opened the project as a workspace
2. Try reloading the VS Code window (**Developer: Reload Window** from the command palette)
3. Verify that your Python interpreter is correctly set (should be `.venv/bin/python`)
4. Check the Pylance language server is running (status should show in the bottom right)

## Python Environment

The project is configured to use a virtual environment in the `.venv` directory. If you haven't created this yet:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate

# Install development dependencies
pip install -e ".[bunny,s3,linode,dev]"
```

## Debugging

For debugging, use the following launch configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Buckia CLI",
            "type": "python",
            "request": "launch",
            "module": "buckia.cli",
            "console": "integratedTerminal",
            "args": [],
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

You can add this to `.vscode/launch.json`.