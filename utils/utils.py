import sys, os

_this_file = os.path.abspath(__file__)
_this_dir = os.path.split(_this_file)[0]
ROOT_DIR = os.path.split(_this_dir)[0]

def isOpenshiftEnv():
    """
    Return True if this appears to be an Openshift Environment.
    """
    MIN_ENV_COUNT = 30
    env_vars = os.environ.keys()
    isOpenshiftEnv = lambda s: 'OPENSHIFT' == s[:9]
    openshift_envs = [e for e in env_vars if isOpenshiftEnv(e)]
    return len(openshift_envs) >= MIN_ENV_COUNT

def fixSysPath():
    sys.path = [ROOT_DIR] + sys.path
