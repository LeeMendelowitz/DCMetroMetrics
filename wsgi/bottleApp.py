#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import bottle
import pymongo
import hotCars
import dbUtils
from StringIO import StringIO
from datetime import datetime

bottle.debug(True)

REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
STATIC_DIR = os.path.join(REPO_DIR, 'wsgi', 'static')
bottle.TEMPLATE_PATH.append(os.path.join(REPO_DIR, 'wsgi', 'views'))

@bottle.route('/')
def index():
    bottle.redirect('/hotcars/all')

@bottle.route('/hotcars/all')
def allHotCars():
    try:
        db = dbUtils.getDB()
        hotCarDict = hotCars.getAllHotCarReports(db)
        return bottle.template('allHotCars',
                           hotCarDict=hotCarDict)
    except Exception as e:
        print 'Caught exception! %s\n'%(str(e))
        raise e

from bottle import static_file
@bottle.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=STATIC_DIR)

@bottle.route('/escalator/<unitId>')
# Make the output slightly more human readable
def printEscalatorStatus(unitId):
    if len(unitId) == 6:
        unitId = '%sESCALATOR'%unitId
    db = dbUtils.getDB()
    escId = dbUtils.unitToEscId.get(unitId, None)
    if escId is None:
        return 'No escalator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId)
    dbUtils.addStatusAttr(statuses)
    escData = dbUtils.escIdToEscData[escId]


    # Summarize the escalator performance
    startTime = datetime(2000,1,1)
    escSummary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=datetime.now())
    return bottle.template('statusListing', unitId = unitId[0:6], escData=escData, statuses=statuses,
                           escSummary=escSummary)

@bottle.route('/DEBUG/cwd')
def dbg_cwd():
  return "<tt>cwd is %s</tt>" % os.getcwd()

@bottle.route('/DEBUG/env')
def dbg_env():
  env_list = ['%s: %s' % (key, value)
              for key, value in sorted(os.environ.items())]
  return "<pre>env is\n%s</pre>" % '\n'.join(env_list)

application = bottle.default_app()
