# Publishing Buckia to PyPI

This guide outlines the steps to publish the Buckia package to the Python Package Index (PyPI).

## Prerequisites

Before publishing to PyPI, ensure you have the following:

1. A PyPI account (register at [https://pypi.org/account/register/](https://pypi.org/account/register/))
2. The latest version of `build` and `twine` installed:
   ```
   uv pip install --upgrade build twine
   ```

## Update Package Information

1. Ensure your package information in `setup.py` is accurate:
   - Update author name and email
   - Update GitHub repository URL (replace `yourusername` with your actual GitHub username)
   - Verify package classifiers are correct

2. Update the version number in `buckia/__init__.py`:
   ```python
   __version__ = "0.x.x"  # Replace with your version
   ```

3. Update the `CHANGELOG.md` to document changes in the new version.

## Build Distribution Packages

Build both source distribution and wheel packages:

```bash
cd /path/to/buckia
uv run -m build
```

This creates two files in the `dist/` directory:
- A source archive (`.tar.gz`)
- A wheel package (`.whl`)

## Test Your Package (Optional but Recommended)

Test the built package locally before uploading to PyPI:

```bash
# Create a virtual environment
uv venv --reset test_env
cd test_env

# Activate the environment
source bin/activate  # Unix/macOS
# OR
.\Scripts\activate  # Windows

# Install the package from the local distribution
uv pip install ../dist/buckia-0.x.x-py3-none-any.whl

# Test importing and basic functionality
python -c "import buckia; print(buckia.__version__)"

# Deactivate when done
deactivate
```

## Upload to Test PyPI (Recommended)

Test the upload process on TestPyPI first:

```bash
uv run -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

You'll be prompted for your TestPyPI username and password.

Then test installing from TestPyPI:

```bash
uv pip install --index-url https://test.pypi.org/simple/ buckia
```

## Upload to PyPI

Once testing is successful, upload to the real PyPI:

```bash
uv run -m twine upload dist/*
```

You'll be prompted for your PyPI username and password.

## Verify the Upload

After uploading, verify your package is available on PyPI:

1. Visit your package page: `https://pypi.org/project/buckia/`
2. Test installation from PyPI:
   ```bash
   uv pip install buckia
   ```

## Using GitHub Actions (Recommended)

Alternatively, you can use the GitHub Actions workflow already configured in `.github/workflows/publish.yml`:

1. Update version and documentation as described above
2. Commit and push your changes
3. Create and push a new tag:
   ```bash
   git tag -a v0.x.x -m "Release version 0.x.x"
   git push origin v0.x.x
   ```
4. The GitHub Actions workflow will automatically build and publish to PyPI

## Maintaining API Tokens

For better security, consider using API tokens instead of your password:

1. Generate an API token on PyPI: https://pypi.org/manage/account/token/
2. Store the token securely (e.g., in your password manager or as a GitHub secret)
3. Use the token instead of your password when uploading:
   ```bash
   uv run -m twine upload dist/* -u __token__ -p pypi-your-token-here
   ```

## Troubleshooting

- **Package name already exists**: Choose a different package name or contact the owner
- **Invalid classifier**: Check the list of valid classifiers at https://pypi.org/classifiers/
- **Upload fails**: Make sure you're not trying to upload a version that already exists
- **README rendering issues**: Check that your README.md is valid Markdown