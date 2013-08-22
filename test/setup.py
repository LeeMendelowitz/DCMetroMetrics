"""
Set environmental variables for local testing.
"""

import os, sys
sout = sys.stdout.write
serr = sys.stderr.write

# 
filePath = os.path.abspath(__file__)
TEST_DIR, fn = os.path.split(filePath)
HOME_DIR = os.path.split(TEST_DIR)[0]

#####################################################
# Define environmental variables
vals = [
    ('OPENSHIFT_DATA_DIR', os.path.join(HOME_DIR, 'data')),
    ('OPENSHIFT_REPO_DIR', HOME_DIR),
    ('OPENSHIFT_MONGODB_DB_USERNAME', "LMM"),
    ('OPENSHIFT_MONGODB_DB_LOG_DIR', os.path.join(HOME_DIR, 'mongodb')),
    ('OPENSHIFT_MONGODB_DB_PASSWORD', "123456"),
    ('OPENSHIFT_MONGODB_DB_HOST', 'localhost'),
    ('OPENSHIFT_MONGODB_DB_PORT', '27017'),
    ('OPENSHIFT_PYTHON_DIR', ''),
    ('OPENSHIFT_HOME_DIR', HOME_DIR),
    ('OPENSHIFT_INTERNAL_IP', 'localhost')
]

dir_keys = ['OPENSHIFT_DATA_DIR', 'OPENSHIFT_REPO_DIR', 'OPENSHIFT_MONGODB_DB_LOG_DIR']
######################################################

def setupEnv():
    print 'Setting up testing environmental variables.'

    # Update the environmental variables
    os.environ.update(vals)

    # Create any of these directories if they do not already exist
    for dk in dir_keys:
        d = os.environ[dk]
        if not os.path.exists(d):
            os.mkdir(d)

def fixSysPath():
    print 'Setting sys.path to include the dcmetrometrics package at: %s'%HOME_DIR
    sys.path = [HOME_DIR] + sys.path

setupEnv()
fixSysPath()
