#!/usr/bin/env python3
"""
Buckia - Multi-platform, multi-backend storage bucket synchronization
"""

import os
from setuptools import setup, find_packages

# Read version from __init__.py
with open(os.path.join('buckia', '__init__.py'), 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break
    else:
        version = '0.4.0'

# Read long description from README.md
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='buckia',
    version=version,
    description='Multi-platform, multi-backend storage bucket synchronization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Henrik Vendelbo',
    author_email='henrik@youremaildomain.com',
    url='https://github.com/yourusername/buckia',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.25.0',
        'pyyaml>=5.4.0',
    ],
    extras_require={
        'bunny': ['bunnycdnpython>=0.0.8'],
        's3': ['boto3>=1.17.0'],
        'linode': ['linode-api4>=5.0.0'],
        'dev': [
            'pytest>=6.2.0',
            'pytest-cov>=2.10.1',
            'pytest-env>=0.8.1',
            'pytest-timeout>=2.1.0',
            'pytest-dotenv>=0.5.2',
            'black>=20.8b1',
            'flake8>=3.8.4',
            'mypy>=0.790',
        ],
    },
    entry_points={
        'console_scripts': [
            'buckia=buckia.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Archiving :: Mirroring',
    ],
    python_requires='>=3.7',
    license='AGPL-3.0',
) 