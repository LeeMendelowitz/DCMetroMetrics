"""
Define global variables.
"""

import os

PY_DIR = os.environ['PYTHON_DIR']
REPO_DIR = os.environ['REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')
DATA_DIR = os.environ['DATA_DIR']
WWW_DIR = os.environ['WWW_DIR']

MONGODB_HOST = os.environ["MONGODB_HOST"]
MONGODB_PORT = int(os.environ["MONGODB_PORT"])
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", None)
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", None)

INTERNAL_SERVE_IP = os.environ["INTERNAL_SERVE_IP"] # Internal IP Address to serve app through.
INTERNAL_SERVE_PORT = os.environ["INTERNAL_SERVE_PORT"] # Internal Port to serve app through.