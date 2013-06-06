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

#####################################################
# Setup MongoDB by adding a user to the database, if necessary
def setupMongoDB():
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]

    # Run mongodb
    # 6/2/2013: NOTE: My macbook is running a mongod instance, so there is no need to start one

#    cmd = ['mongod', '--dbpath', dbpath]
#    devnull = open(os.devnull, 'w')
#    p_mongod = subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
#
#    serr("Setting Up MongoDB. Sleeping...")
#    time.sleep(5)
#    serr("DONE!\n")

    # Add the user to the admin db
    try:
        #serr('ADDING NEW ADMIN USER\n')
        host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
        port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
        user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
        password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
        client = MongoClient(host, port, j=True)
        db = client.admin
        res = db.add_user(user, password, roles=['userAdminAnyDatabase', 'readWriteAnyDatabase','dbAdminAnyDatabase'])
        #serr('DONE ADDING NEW ADMIN USER. Returned: %s\n'%(str(res)))
#        db = client.dummy
#        res = db.add_user(user, password, roles=['readWrite', 'dbAdmin', 'userAdmin'])
        db = client.testDB
        db.dummy.remove()
        db.dummy.insert({'firstName':'Lee', 'lastName':'Mendelowitz'})

        # Clear out the collections
        db = client.MetroEscalators
        db.hotcars.remove()
        db.hotcars_tweets.remove()
        db.hotcars_appstate.remove()

        client.close()

        #serr('Closed Client\n')

    except Exception as e:
        serr('Caught Exception: %s\n'%str(e))

#    p_mongod.kill()
    #p_mongod.wait()

p_mongod = None

def runMongod():
    global p_mongod
    serr("Running MongoD. Sleeping...")
    sys.stderr.flush()
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]

    # Run mongodb
    cmd = ['mongod', '--dbpath', dbpath, '--auth']
    devnull = open(os.devnull, 'w')
    p_mongod = subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
    time.sleep(5)
    serr("DONE!\n")
    sys.stderr.flush()

def testConnectMongoDB():
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]
    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = MongoClient(host, port)

    # Try authenticating with admin
    db = client.admin
    #serr('Attempting Authentication\n')
    res = db.authenticate(user, password)
    #serr('Authenticate returned: %s\n'%str(res))

    # Try getting data from dummy collection
    db = client.testDB
    cursor = db.dummy.find()
    count = cursor.count()
    if count == 0:
        raise RuntimeError("Found no records in dummy database")

def killMongod():
    if p_mongod:
        p_mongod.kill()
        p_mongod.wait()

def startup():
    print 'IN STARTUP'
    setupPaths()
    setupMongoDB()
    # 6/2/2013: NOTE: My macbook is running a mongod instance, so there is no need to start one
    #runMongod()
    try:
       testConnectMongoDB()
    except Exception:
        sys.stderr.write('Caught Exception: %s\n'%(str(e)))
    print 'DONE STARTUP'

def shutdown():
    print 'IN SHUTDOWN'
    # 6/2/2013: NOTE: My macbook is running a mongod instance, so there is no need to start one
    #killMongod()

def getDB():
    dbpath = os.environ["OPENSHIFT_MONGODB_DB_LOG_DIR"]
    host = os.environ["OPENSHIFT_MONGODB_DB_HOST"]
    port = int(os.environ["OPENSHIFT_MONGODB_DB_PORT"])
    user = os.environ["OPENSHIFT_MONGODB_DB_USERNAME"]
    password = os.environ["OPENSHIFT_MONGODB_DB_PASSWORD"]
    client = MongoClient(host, port)

    # Try authenticating with admin
    db = client.admin
    #serr('Attempting Authentication\n')
    res = db.authenticate(user, password)
    #serr('Authenticate returned: %s\n'%str(res))

    db = client.MetroEscalators
    return db
