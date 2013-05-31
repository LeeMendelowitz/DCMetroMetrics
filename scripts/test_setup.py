# Perform any setup for local testing
# This includes setting any environmental variables,
# and running a pymongo

import os
import sys
sout = sys.stdout.write
serr = sys.stderr.write
import subprocess
import pymongo
import time
from pymongo import MongoClient

cwd = os.getcwd()
home_dir = os.path.split(cwd)[0]

#####################################################
# Define environmental variables
vals = [
    ('OPENSHIFT_DATA_DIR', os.path.join(home_dir, 'data')),
    ('OPENSHIFT_REPO_DIR', home_dir),
    ('OPENSHIFT_MONGODB_DB_USERNAME', "LMM"),
    ('OPENSHIFT_MONGODB_DB_LOG_DIR', os.path.join(home_dir, 'mongodb')),
    ('OPENSHIFT_MONGODB_DB_PASSWORD', "123456"),
    ('OPENSHIFT_MONGODB_DB_HOST', 'localhost'),
    ('OPENSHIFT_MONGODB_DB_PORT', '27017')
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

#####################################################
# Setup MongoDB by adding a user to the database, if necessary
def setupMongoDB():
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]

    # Run mongodb
    cmd = ['mongod', '--dbpath', dbpath, '--journal']
    p_mongod = subprocess.Popen(cmd)

    serr("RUNING MONGOD. Sleeping...")
    time.sleep(5)
    serr("DONE SLEEP\n")

    # Add the user to the admin db
    try:
        serr('ADDING NEW ADMIN USER\n')
        sys.stderr.flush()
        host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
        port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
        user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
        password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
        client = MongoClient(host, port, j=True)
        db = client.admin
        res = db.add_user(user, password, roles=['userAdminAnyDatabase', 'readWriteAnyDatabase','dbAdminAnyDatabase'])
        serr('DONE ADDING NEW ADMIN USER. Returned: %s\n'%(str(res)))
#        db = client.dummy
#        res = db.add_user(user, password, roles=['readWrite', 'dbAdmin', 'userAdmin'])
        db = client.testDB
        db.dummy.remove()
        db.dummy.insert({'firstName':'Lee', 'lastName':'Mendelowitz'})
        sys.stderr.flush()
        sys.stdout.flush()
        client.close()

        serr('Closed Client\n')
        sys.stderr.flush()

    except Exception as e:
        serr('Caught Exception: %s\n'%str(e))
        sys.stderr.flush()

    p_mongod.kill()
    p_mongod.wait()

p_mongod = None

def runMongod():
    global p_mongod
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]

    # Run mongodb
    cmd = ['mongod', '--dbpath', dbpath, '--auth', '--journal']
    devnull = open(os.devnull, 'w')
    p_mongod = subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
    time.sleep(5)

def testConnectMongoDB():
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]
    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = MongoClient(host, port)

    # Try authenticating with admin
    db = client.admin
    serr('Attempting Authentication\n')
    sys.stderr.flush()
    res = db.authenticate(user, password)
    serr('Authenticate returned: %s\n'%str(res))

    # Try getting data from dummy collection
    db = client.testDB
    cursor = db.dummy.find()
    for item in cursor:
        print item
    serr('Found records: %i\n'%cursor.count())

def killMongod():
    if p_mongod:
        p_mongod.kill()
        p_mongod.wait()

def startup():
    setupPaths()
    setupMongoDB()
    runMongod()
    try:
       testConnectMongoDB()
    except Exception as e:
        sys.stderr.write('Caught Exception: %s\n'%(str(e)))

def shutdown():
    killMongod()

def getDB():
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]
    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = MongoClient(host, port)

    # Try authenticating with admin
    db = client.admin
    serr('Attempting Authentication\n')
    sys.stderr.flush()
    res = db.authenticate(user, password)
    serr('Authenticate returned: %s\n'%str(res))

    db = client.MetroEscalators
    return db
