import os
import sys
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')
sys.path.append(SCRIPT_DIR)
