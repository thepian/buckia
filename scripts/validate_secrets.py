#!/usr/bin/env python3
"""
Validates that required secrets are set for testing.
"""

import os
import sys

# List of required secret environment variables
REQUIRED_SECRETS = [
    'BUNNY_API_KEY',
    'BUNNY_STORAGE_API_KEY'
]

# Check for missing secrets
missing_secrets = [k for k in REQUIRED_SECRETS if not os.environ.get(k)]

# Exit with error if any secrets are missing
if missing_secrets:
    print(f'Error: Missing required secrets: {missing_secrets}', file=sys.stderr)
    sys.exit(1)
else:
    print("All required secrets are set.")
    sys.exit(0)