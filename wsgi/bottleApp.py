#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import bottle
import pymongo
import hotCars
import dbUtils

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
