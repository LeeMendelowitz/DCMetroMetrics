#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import bottle
import pymongo
from StringIO import StringIO
from datetime import datetime
from operator import itemgetter
from collections import defaultdict, Counter

import metroEscalatorsWeb
import hotCarsWeb
import stations

#bottle.debug(True)

REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']
STATIC_DIR = os.path.join(REPO_DIR, 'wsgi', 'static')
DYNAMIC_DIR = os.path.join(DATA_DIR, 'webpages', 'dynamic')
bottle.TEMPLATE_PATH.append(os.path.join(REPO_DIR, 'wsgi', 'views'))

########################################
@bottle.route('/')
def index():
    filename = 'home.html'
    return static_file(filename, root=DYNAMIC_DIR)

########################################
@bottle.route('/hotcars')
def hotCars():
    filename = 'hotcars.html'
    return static_file(filename, root=DYNAMIC_DIR)

########################################
@bottle.route('/hotcars/<carNum>')
def hotCar(carNum):
    filename = 'hotcar_%s.html'%carNum
    return static_file(filename, root=DYNAMIC_DIR)

########################################
from bottle import static_file
@bottle.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=STATIC_DIR)

########################################
@bottle.route('/escalators/<unitId>')
def genEscalatorStatus(unitId):
    filename = 'escalator_%s.html'%unitId
    return static_file(filename, root=DYNAMIC_DIR)

###############################################
@bottle.route('/stations/<shortName>')
def stationStatus(shortName):
    filename = 'station_%s.html'%shortName
    return static_file(filename, root=DYNAMIC_DIR)

###############################################
@bottle.route('/escalators/directory')
def allEscalators():
    filename = 'escalators.html'
    return static_file(filename, root=DYNAMIC_DIR)

###############################################
@bottle.route('/escalators')
@bottle.route('/escalators/outages')
def escalatorOutages():
    filename = 'escalatorOutages.html'
    return static_file(filename, root=DYNAMIC_DIR)

###############################################
@bottle.route('/escalators/rankings')
def escalatorRankings():
    filename = 'escalatorRankings.html'
    return static_file(filename, root=DYNAMIC_DIR)

@bottle.route('/escalators/rankingsTable')
def escalatorRankingsTable():
    filename = 'escalatorRankingsTable.html'
    return static_file(filename, root=DYNAMIC_DIR)

###############################################
@bottle.route('/stations')
# Listing of all stations
def stationListing():
    filename = 'stations.html'
    return static_file(filename, root=DYNAMIC_DIR)

########################################
@bottle.route('/glossary')
def glossary():
    filename = 'glossary.html'
    return static_file(filename, root=DYNAMIC_DIR)

application = bottle.default_app()
