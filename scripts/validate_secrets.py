#!/usr/bin/env python3
"""
Validates that required secrets are set for testing.
"""

import os
import sys

# Required secrets: check both the uppercase canonical name and the lowercase variant
# The workflow exports buckia_buckia_demo (lowercase); Linux env vars are case-sensitive.
REQUIRED_SECRETS = [
    ("BUNNY_API_KEY", "BUNNY_API_KEY"),
    ("BUCKIA_BUCKIA_DEMO", "buckia_buckia_demo"),
]

missing_secrets = [
    canonical
    for canonical, alt in REQUIRED_SECRETS
    if not os.environ.get(canonical) and not os.environ.get(alt)
]

# Exit with error if any secrets are missing
if missing_secrets:
    print(f"Error: Missing required secrets: {missing_secrets}", file=sys.stderr)
    sys.exit(1)
else:
    print("All required secrets are set.")
    sys.exit(0)
