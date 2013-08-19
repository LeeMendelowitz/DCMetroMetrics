"""
Set environmental variables for local testing.
"""

import os
import sys
sout = sys.stdout.write
serr = sys.stderr.write

cwd = os.getcwd()
home_dir = os.path.split(cwd)[0]
home_dir = cwd

#####################################################
# Define environmental variables
vals = [
    ('OPENSHIFT_DATA_DIR', os.path.join(home_dir, 'data')),
    ('OPENSHIFT_REPO_DIR', home_dir),
    ('OPENSHIFT_MONGODB_DB_USERNAME', "LMM"),
    ('OPENSHIFT_MONGODB_DB_LOG_DIR', os.path.join(home_dir, 'mongodb')),
    ('OPENSHIFT_MONGODB_DB_PASSWORD', "123456"),
    ('OPENSHIFT_MONGODB_DB_HOST', 'localhost'),
    ('OPENSHIFT_MONGODB_DB_PORT', '27017'),
    ('OPENSHIFT_PYTHON_DIR', ''),
    ('OPENSHIFT_HOME_DIR', home_dir),
    ('OPENSHIFT_INTERNAL_IP', 'localhost')
]

dir_keys = ['OPENSHIFT_DATA_DIR', 'OPENSHIFT_REPO_DIR', 'OPENSHIFT_MONGODB_DB_LOG_DIR']
######################################################

def setupPaths():
# Update the environmental variables
    os.environ.update(vals)

# Create any of these directories if they do not already exist
    for dk in dir_keys:
        d = os.environ[dk]
        if not os.path.exists(d):
            os.mkdir(d)

setupPaths()
