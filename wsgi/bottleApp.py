#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import bottle
import pymongo
import hotCars
import dbUtils
from StringIO import StringIO

bottle.debug(True)

bottle.TEMPLATE_PATH.append(os.path.join(os.environ['OPENSHIFT_REPO_DIR'],
                                         'wsgi', 'views'))

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

@bottle.route('/escalator/<unitId>')
# TO DO: Make this a template. 
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
    def statusToString(s):
        totalTime = 'N/A'
        endTime = s.get('end_time', None)
        if endTime is not None:
            totalTime = endTime - s['time']
            totalTime = '%.1f sec'%totalTime.total_seconds()
        else:
            endTime = 'N/A'
        out = StringIO()
        out.write('<tr>\n')
        outS = '<td>{s[time]}</td><td>{s[symptom]}</td><td>{endTime}</td><td>{totalTime}</td>\n'
        outS = outS.format(s=s, endTime=endTime, totalTime = totalTime)
        out.write(outS)
        out.write('</tr>\n')
        outS = out.getvalue()
        out.close()
        return outS
    out = StringIO()
    out.write('<html><body>\n')
    out.write('<table border=1>')
    for s in statuses:
        out.write('<p>%s</p>\n'%statusToString(s))
    out.write('</table>')
    out.write('</body></html>\n')
    outS = out.getvalue()
    out.close()
    return outS

@bottle.route('/DEBUG/cwd')
def dbg_cwd():
  return "<tt>cwd is %s</tt>" % os.getcwd()

@bottle.route('/DEBUG/env')
def dbg_env():
  env_list = ['%s: %s' % (key, value)
              for key, value in sorted(os.environ.items())]
  return "<pre>env is\n%s</pre>" % '\n'.join(env_list)

@bottle.route('/static/:filename')
def static_file(filename):
  bottle.send_file(filename,
                   root= os.path.join(os.environ['OPENSHIFT_REPO_DIR'],
                                      'wsgi', 'static'))

application = bottle.default_app()
