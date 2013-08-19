"""
web.webPageGenerator

This module provides functionality to generate webpages as static html
pages. They are stored in the XXX directory, and served by the bottleApp.

DCMetroMetrics webpages are implemented as bottle templates, which are
documents with html/javascript code with embedded python.
An effort has been made to keep the bottle templates as simple as possible,
with most functionality residing in (hotcars), (eles) (POINT TO THE RIGHT MODULES).

Each webpage has an entry in the MongoDB webpages collection.

The WebPageGenerator class is an app which periodically looks for webpages which
need to be updated. A webpage is updated if it goes stale (i.e. has not been updated for X hours),
or if it's doc['forceUpdate'] == True.

The classToUpdateInterval dict specifies how often pages of each class are automatically updated.

The 'forceUpdate' attribute of webpage docs are changed by events which take place in
the elevatorApp, escalatorApp, and hotCarApp (such as an escalator breaking, or a 
hot car being reported).

Page Generators
================
This module implements a function to generate each web page on the DCMetroMetrics site.
These functions have the prototype:
def genXPage(doc, dbg), where:
    - doc is a document from the MongoDB webpages collection
    - dbg is an instance of dbGlobals.DBGlobals
For example, see funtions genEscalatorPage and genEscalatorRankings

The classToPageGenerator dict maps a webpage doc's class attribute
to the page generator function which should be used to generate the page.

Development/Testing
===================
During testing/development, these functions will prove useful:
updatePage(doc, dbg): Trigger an update the page specified by the webpage doc
updateAllPages(): Trigger an update all webpages
reload(): reload the bottle module

If changes are made to the bottle templates, call the reload function
of this module to reload the bottle module and get the updated templates.

My recipe for local development/testing:
- Run a local web server by running the bottleApp
- Make changes to the bottle templates or to this module
- In ipython:
    reload(WebPageGenerator) # Get latest version of module
    WebPageGenerator.reload() # Reload the bottle templates
    WebPageGenerator.updatePage(...) # Regenerate the web pages of interest 
- Point your browser to: http://localhost:8080/ and view the changes to the site.
====================================================================================
"""

import os
import sys
from datetime import datetime, timedelta
import gevent
import bottle
from operator import itemgetter
from collections import defaultdict, Counter
import __builtin__

from ..common import dbGlobals, stations
from ..common.metroTimes import utcnow, toLocalTime, localToUTCTime, tzutc
from ..common.restartingGreenlet import RestartingGreenlet
from ..eles import dbUtils
from . import eles as elesWeb
from . import hotcars as hotCarsWeb
from ..hotcars import hotCars
from ..third_party import gviz_api


# Set the path to the bottle template directory
REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']
STATIC_DIR = os.path.join(REPO_DIR, 'wsgi', 'static')
WEBPAGE_DIR = os.path.join(DATA_DIR, 'webpages')
DYNAMIC_DIR = os.path.join(WEBPAGE_DIR, 'dynamic')
bottle.TEMPLATE_PATH.append(os.path.join(REPO_DIR, 'wsgi', 'views'))

if not os.path.exists(WEBPAGE_DIR):
    os.mkdir(WEBPAGE_DIR)

if not os.path.exists(DYNAMIC_DIR):
    os.mkdir(DYNAMIC_DIR)


# Update time in hours
classToUpdateInterval = \
{
    'escalator' : 1,
    'escalatorRankings': 6,
    'escalatorDirectory' : 1,
    'escalatorOutages' : 1,
    'stationDirectory' : 1,
    'station': 1,
    'hotcars' : 1,
    'hotcar' : 1,
    'glossary' : 6,
    'data'  : 6,
    'home' : 6
}


################################################
# Reload the essential parts of this module.
# Useful for testing. Call this after editing
# a bottle template file in order to generate
# a page using the updated template.
#
# Warning: This function is redefining the python "reload" object
# from the python builtin for this module. The builtin reload
# function is still available through __builtin__ module.
def reload():
    """ 
    Reload the essential parts of the webPageGenerator module
    """
    __builtin__.reload(bottle)
    bottle.TEMPLATE_PATH.append(os.path.join(REPO_DIR, 'wsgi', 'views'))
    __builtin__.reload(elesWeb)
    __builtin__.reload(hotCarsWeb)
    __builtin__.reload(hotCars)

##############################
# Make a wrapper around the bottle.template call
def makePage(*args, **kwargs):
    curTime = toLocalTime(utcnow())
    kwargs['curTime'] = curTime
    return bottle.template(*args, **kwargs)

###################################################
# Initialize the webpages collection in the database
def initDB(dbg):

    db = dbg.getDB()

    queries = []

    # The home page
    queries.append({'class' : 'home'})

    # All escalators get a page.
    escIds = dbg.getEscalatorIds()
    for escId in escIds:
        queries.append({'class' : 'escalator', 'escalator_id' : escId})

    eleIds = dbg.getElevatorIds()
    for eleId in eleIds:
        queries.append({'class' : 'elevator', 'elevator_id' : eleId})

    # All stations get a page.
    stationShortNames = list(set(sd['shortName'] for sd in stations.codeToStationData.itervalues()))
    for stationName in stationShortNames:
        queries.append({'class' : 'station', 'station_name' : stationName})

    # The rankings get a page
    queries.append({'class' : 'escalatorRankings'})

    # The stationDirectory gets a page
    queries.append({'class' : 'stationDirectory'})

    # The escalator listing gets a page
    queries.append({'class' : 'escalatorDirectory'})

    # The escalator listing gets a page
    queries.append({'class' : 'elevatorDirectory'})

    # The non-operational listing gets a page
    queries.append({'class' : 'escalatorOutages'})

    # The hotcars page
    queries.append({'class' : 'hotcars'})

    # The glossary
    queries.append({'class' : 'glossary'})

    # The Data downloads page
    queries.append({'class' : 'data'})

    # The Press page
    queries.append({'class' : 'press'})

    # The page for each hotcars
    hotCarNums = db.hotcars.distinct('car_number')
    for carNum in hotCarNums:
        queries.append({'class' : 'hotcar', 'car_number' : carNum})

    # Update the database if a document does not exist
    for q in queries:
        insert = dict(q)
        insert['forceUpdate'] = True
        if db.webpages.find(q).count() == 0:
            db.webpages.insert(insert)

################################################################################
# Define functions to generate webpage content, given a doc
# from the webpages collection

#########
def genEscalatorPage(doc, dbg):
    escId = doc['escalator_id']
    escUnitName = dbg.escIdToUnit[escId]
    escUnitShort = escUnitName[0:6]
    db = dbg.getDB()
    if escId is None:
        return 'No escalator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId, dbg=dbg)
    dbUtils.addStatusAttr(statuses, dbg=dbg)

    curTime = utcnow()
    # Set the end_time of the current status to now
    if statuses and 'end_time' not in statuses[0]:
        statuses[0]['end_time'] = curTime

    escData = dbg.escIdToEscData[escId]

    # Summarize the escalator performance
    startTime =  statuses[-1]['time'] if statuses else localToUTCTime(datetime(2000,1,1))
    escSummary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=curTime)

    # Generate the page
    content = makePage('escalator', unitId = escUnitShort, escData=escData, statuses=statuses, escSummary=escSummary)
    filename = 'escalator_%s.html'%(escUnitShort)
    writeContent(filename, content)

#######################################
def genElevatorPage(doc, dbg):
    escId = doc['elevator_id']
    escUnitName = dbg.escIdToUnit[escId]
    escUnitShort = escUnitName[0:6]
    db = dbg.getDB()
    if escId is None:
        return 'No elevator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId, dbg=dbg)
    dbUtils.addStatusAttr(statuses, dbg=dbg)

    curTime = utcnow()
    # Set the end_time of the current status to now
    if statuses and 'end_time' not in statuses[0]:
        statuses[0]['end_time'] = curTime

    escData = dbg.escIdToEscData[escId]

    # Summarize the escalator performance
    startTime =  statuses[-1]['time'] if statuses else localToUTCTime(datetime(2000,1,1))
    escSummary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=curTime)

    # Generate the page
    content = makePage('elevator', unitId = escUnitShort, escData=escData, statuses=statuses, escSummary=escSummary)
    filename = 'elevator_%s.html'%(escUnitShort)
    writeContent(filename, content)



#########
def genStationPage(doc, dbg):
    # Get the station code
    shortName = doc['station_name']
    codes = [c for c,sn in stations.codeToShortName.iteritems() if sn==shortName]
    if not codes:
        return 'No station found'
    stationCode = codes[0]

    # Get the summary for this station over all time
    stationSummary = dbUtils.getStationSummary(stationCode, dbg=dbg)

    # Get the current overview of escalators in this station
    stationSnapshot = dbUtils.getStationSnapshot(stationCode, dbg=dbg)
    escUnitIds = stationSummary['escUnitIds']
    escToSummary = stationSummary['escToSummary']
    escToStatuses = stationSummary['escToStatuses']

    # Generate the table listing of escalators
    escalatorListing = []
    for escUnitId in escUnitIds:
        escSummary = escToSummary.get(escUnitId, {})
        statuses = escToStatuses[escUnitId]
        if not statuses:
            continue
        latestStatus = statuses[0]
        escId = dbg.unitToEscId[escUnitId]
        escMetaData = dbg.escIdToEscData[escId]
        shortUnitId = escUnitId[0:6]
        rec = {'unitId' : shortUnitId,
               'stationDesc' : escMetaData['station_desc'],
               'escDesc' : escMetaData['esc_desc'],
               'curStatus' : latestStatus['symptom'],
               'curSymptomCategory' : latestStatus['symptomCategory'],
               'availability' : escSummary['availability']} 
        escalatorListing.append(rec)

    escalatorListing = sorted(escalatorListing, key = itemgetter('unitId'))
    content = makePage('station', stationSummary=stationSummary,
        stationSnapshot=stationSnapshot, escalators=escalatorListing)
    filename = 'station_%s.html'%(shortName)
    writeContent(filename, content)

#########
def genEscalatorRankings_Old(doc):
    rankingDict = elesWeb.getRankings()
    compiledRankings = elesWeb.compileRankings(rankingDict)
    stationCodeToSummary = elesWeb.getStationSummaries()
    dtStationRankings = elesWeb.makeStationRankingGoogleTable(stationCodeToSummary)
    content = makePage('escalatorRankings', rankings=compiledRankings, dtStationRankings=dtStationRankings)
    filename = 'escalatorRankings.html'
    writeContent(filename, content)

###################################
def genEscalatorRankings(doc, dbg):
    now = utcnow()
    rankingArgs = [
                     #key,  (startTime, endTime, dbg),       header value
                    ('d1', (now - timedelta(days=1), now, dbg), '1 day'),
                    ('d3', (now - timedelta(days=3), now, dbg), '3 day'),
                    ('d7', (now - timedelta(days=7), now, dbg), '7 day'),
                    ('d14', (now - timedelta(days=14), now, dbg), '14 day'),
                    ('d28', (now - timedelta(days=28), now, dbg), '28 day'),
                    ('AllTime', (None, None), 'All Time') ]
    def makeEntry(args, header):
        dt = elesWeb.escalatorRankingsTable(*args)
        return {'dataTable' : dt,
                'json' : dt.ToJSon(),
                'header' : header}

    rankingsDict = dict((k, makeEntry(args, header)) for k,args,header in rankingArgs)
    dtDailyCounts = elesWeb.makeBreakInspectionTable(dbg=dbg)
    stationCodeToSummary = elesWeb.getStationSummaries(dbg=dbg)
    dtStationRankings = elesWeb.makeStationRankingGoogleTable(stationCodeToSummary)

    # Write html
    content = makePage('escalatorRankings', rankingsDict = rankingsDict, dtDailyCounts=dtDailyCounts, dtStationRankings=dtStationRankings)
    filename = 'escalatorRankings.html'
    writeContent(filename, content)

    # Write javacsript
    content = makePage('escalatorRankings_js', rankingsDict=rankingsDict, dtDailyCounts=dtDailyCounts, dtStationRankings=dtStationRankings)
    filename = 'escalatorRankings.js'
    writeContent(filename, content)

#########
def genHomePage(doc, dbg):
    content = makePage('home')
    filename = 'home.html'
    writeContent(filename, content)

#########
def genDataPage(doc, dbg):
    content = makePage('data')
    filename = 'data.html'
    writeContent(filename, content)

#########
def genPressPage(doc, dbg):
    content = makePage('press')
    filename = 'press.html'
    writeContent(filename, content)

#####################################################
# Generate the escalator outages page.
# Doc is the record for this page in the db.webpages collection.
def genEscalatorOutages(doc, dbg):

    db = dbg.getDB()

    escalatorList = elesWeb.escalatorNotOperatingList()

    # Summarize the non-operational escalators by symptom
    symptomCounts = Counter(esc['symptom'] for esc in escalatorList)

    # Generate the data for the Google Chart pi chart

    # Get data for the Outage Categories summary
    schema = [('symptom', 'string', 'Outage Symptom' ), ('count', 'number', 'Count')]
    data = symptomCounts.items()
    dtSymptoms = gviz_api.DataTable(schema, data=data)

    # Convert the unitId and stationName into html links
    for d in escalatorList:
        d['unitIdHtml'] = elesWeb.makeEscalatorLink(d['unitId'])
        d['stationNameHtml'] = elesWeb.makeStationLink(d['stationCode'])
    escalatorList

    # Get data for the Escalator Outage table
    schema = [('escId', 'string', 'Escalator'),
              ('station', 'string', 'Station'),
              ('entrance', 'string', 'Entrance'),
              ('escDesc', 'string', 'Description'),
              ('status', 'string', 'Status')]
    schemaKeys = ['unitIdHtml', 'stationNameHtml', 'stationDesc', 'escDesc', 'symptom']
    outageTableData = [[d[k] for k in schemaKeys] for d in escalatorList]
    dtOutages = gviz_api.DataTable(schema, data=outageTableData)

    def getOutageClass(d):
        sympCat = d['symptomCategory'].lower()
        return elesWeb.symptomCategoryToClass[sympCat] 
    dtOutagesRowClasses = [getOutageClass(d) for d in escalatorList]


    # Get the availability and weighted availability
    systemAvailability = dbUtils.getSystemAvailability(escalators=True, dbg=dbg)
    kwargs = {'escList' : escalatorList,
              'symptomCounts' : symptomCounts,
              'systemAvailability' : systemAvailability,
              'dtSymptoms' : dtSymptoms,
              'dtOutages' : dtOutages,
              'dtOutagesRowClasses' : dtOutagesRowClasses
             }

    # Make html
    content = makePage('escalatorOutages', **kwargs)
    filename = 'escalatorOutages.html'
    writeContent(filename, content)

    # Make javascript
    content = makePage('escalatorOutages_js', **kwargs)
    filename = 'escalatorOutages.js'
    writeContent(filename, content)

#########
def genEscalatorDirectory(doc, dbg):
    escalatorList = elesWeb.escalatorList(dbg=dbg, escalators=True)

    # Group escalators by station
    stationToEsc = defaultdict(list)
    for esc in escalatorList:
        stationToEsc[esc['stationName']].append(esc)

    # Sort each escalators stations in ascending order by code
    for k,escList in stationToEsc.iteritems():
        stationToEsc[k] = sorted(escList, key = itemgetter('unitId'))

    content = makePage('escalators', stationToEsc=stationToEsc)
    filename = 'escalators.html'
    writeContent(filename, content)

#########
def genElevatorDirectory(doc, dbg):
    elevatorList = elesWeb.escalatorList(elevators=True, dbg=dbg)

    # Group escalators by station
    stationToEsc = defaultdict(list)
    for esc in elevatorList:
        stationToEsc[esc['stationName']].append(esc)

    # Sort each escalators stations in ascending order by code
    for k,escList in stationToEsc.iteritems():
        stationToEsc[k] = sorted(escList, key = itemgetter('unitId'))

    content = makePage('elevators', stationToEsc=stationToEsc)
    filename = 'elevators.html'
    writeContent(filename, content)

#########
def genStationDirectory(doc, dbg):
    stationRecs, dtStations = elesWeb.stationList()

    # Make HTML
    content = makePage('stations', stationRecs=stationRecs, dtStations = dtStations)
    filename = 'stations.html'
    writeContent(filename, content)

    # Make javascript
    content = makePage('stations_js', stationRecs=stationRecs, dtStations = dtStations)
    filename = 'stations.js'
    writeContent(filename, content)

#########
def genHotCars(doc, dbg):

    db = dbg.getDB()

    hotCarData = hotCarsWeb.getAllHotCarData(db)
    dtHotCars = hotCarsWeb.hotCarGoogleTable(hotCarData)
    dtHotCarsByUser = hotCarsWeb.hotCarByUserGoogleTable(db)
    allReports = [r for d in hotCarData.itervalues() for r in d['reports']]
    summary = hotCars.summarizeReports(db, allReports)
    dtHotCarsBySeries = hotCarsWeb.makeCarSeriesGoogleTable(summary['seriesToCount'])
    dtHotCarsByColorCustom = hotCarsWeb.makeColorCountsGoogleTableCustom(summary['colorToCount'])
    dtHotCarsByColor = hotCarsWeb.makeColorCountsGoogleTable(summary['colorToCount'])
    dtHotCarsTimeSeries = hotCarsWeb.makeHotCarTimeSeries(db)
    numReports = sum(d['numReports'] for d in hotCarData.itervalues())

    kwargs = { 'summary' : summary,
               'hotCarData' : hotCarData,
               'dtHotCars' : dtHotCars,
               'dtHotCarsByUser' : dtHotCarsByUser,
               'dtHotCarsBySeries' : dtHotCarsBySeries,
               'dtHotCarsByColor' : dtHotCarsByColor,
               'dtHotCarsByColorCustom' : dtHotCarsByColorCustom,
               'dtHotCarsTimeSeries' : dtHotCarsTimeSeries
             }

    # Write hotCars
    content = makePage('hotCars', **kwargs)
    filename = 'hotcars.html'
    writeContent(filename, content)

    # Write javascript
    content = makePage('hotCars_js', **kwargs)
    filename = 'hotCars.js'
    writeContent(filename, content)

def genGlossaryPage(doc, dbg):
    content = makePage('glossary')
    filename = 'glossary.html'
    writeContent(filename, content)

def genHotCarPage(doc, dbg):
    db = dbg.getDB()

    carNum = int(doc['car_number'])
    data = hotCarsWeb.getHotCarData(db, carNum)
    reports = data['reports']
    colors = data['colors']
    numReports = data['numReports']
    if data['reports']:
        lastReportTime = max(r['time'] for r in data['reports'])
        lastReportTimeStr = hotCarsWeb.formatTimeStr(lastReportTime)
    else:
        lastReportTimeStr = 'N/A'
    content = makePage('hotCar', carNum=carNum, numReports=numReports, lastReportTimeStr=lastReportTimeStr, reports=reports, colors=colors)
    filename = 'hotcar_%i.html'%carNum
    writeContent(filename, content)

########################################
# Write content to the file filename.
# This takes care of selecting the destination
def writeContent(filename, content):
    destDir = DYNAMIC_DIR
    if not os.path.exists(destDir):
        os.mkdir(destDir)
    outFile = os.path.join(destDir, filename)
    with open(outFile, 'w') as fout:
        fout.write(content.encode(encoding='utf-8', errors='ignore'))
##################################################################

class WebPageGenerator(RestartingGreenlet):

    def __init__(self, SLEEP=10):
        RestartingGreenlet.__init__(self, SLEEP=SLEEP)
        self.SLEEP = SLEEP
        self.logFileName = os.path.join(DATA_DIR, 'webPageGenerator.log')
        self.logFile = None
        self.dbg = dbGlobals.DBGlobals()

    def _run(self):
        while True:
            self.logFile = open(self.logFileName, 'a')
            try:
                self.tick()
            except Exception as e:
                self.logFile.write('Web Page Generator caught Exception: %s\n'%str(e))
                import traceback
                tb = traceback.format_exc()
                self.logFile.write('Traceback:\n%s\n\n'%tb)
            self.logFile.close()
            gevent.sleep(self.SLEEP)

    def tick(self):

        dbg = self.dbg
        dbg.update()
        db = dbg.getDB()

        initDB(dbg) # Add any missing documents to the database
       
        # Get documents that need to be updated 
        docs = list(db.webpages.find({'forceUpdate' : True}))

        # Get documents with no lastUpdateTime field
        docs.extend(db.webpages.find({'lastUpdateTime' : {'$exists' : False}}))

        # Get stale documents
        curTime = utcnow()
        curTimeLocal = toLocalTime(curTime)
        staleDocs = []
        for doc in db.webpages.find():
            gevent.sleep(0.0)
            lastUpdateTime = doc.get('lastUpdateTime', None)
            if lastUpdateTime is None:
                continue
            lastUpdateTime = lastUpdateTime.replace(tzinfo=tzutc)
            updateInterval = classToUpdateInterval.get(doc['class'], None) #in hours
            if updateInterval is None:
                continue
            if (curTime - lastUpdateTime).total_seconds() > 3600*updateInterval:
                staleDocs.append(doc)

        docs.extend(staleDocs)

        # Make the document list unique
        seen = set()
        docs = [d for d in docs if not (d['_id'] in seen or seen.add(d['_id']))]

        # Make the updates
        for doc in docs:
           gevent.sleep(0.0) # Cooperative yield
           updatePage(doc, dbg, curTimeLocal, self.logFile)
           #Update the webpage database
           newDoc = dict(doc)
           newDoc['lastUpdateTime'] = utcnow()
           newDoc['forceUpdate'] = False
           db.webpages.update({'_id' : doc['_id']}, newDoc)

classToPageGenerator =  \
    { 'escalator' : genEscalatorPage,
      'escalatorRankings' : genEscalatorRankings,
      'escalatorDirectory': genEscalatorDirectory,
      'escalatorOutages' : genEscalatorOutages,
      'elevatorDirectory' : genElevatorDirectory,
      'elevator' : genElevatorPage,
      'stationDirectory' : genStationDirectory,
      'station' : genStationPage,
      'hotcars' : genHotCars,
      'hotcar' : genHotCarPage,
      'glossary' : genGlossaryPage,
      'data' : genDataPage,
      'press' : genPressPage,
      'home' : genHomePage
    }


############################################
# Re-generate a single webpage, specified by the document from
# the db.webpages collection
def updatePage(doc, dbg, curTimeLocal = None, logFile = sys.stdout):
    """
    Re-generate the webpage given by doc.
    """
    pageGenerator = classToPageGenerator.get(doc['class'], None)
    if pageGenerator is None:
       raise RuntimeError('No page generator for webpage with class %s'%doc['class'])

    if curTimeLocal is None:
        curTimeLocal = toLocalTime(utcnow())
    #Generate the webpage
    tf = '%m/%d/%y %I:%M %p'
    timeStamp = curTimeLocal.strftime(tf)
    logFile.write("%s: Updating webpage: %s\n"%(timeStamp,str(doc)))
    pageGenerator(doc, dbg)

#############################################
# Re-generate all webpages
def updateAllPages():
    """
    Re-generate all webpages
    """
    reload()
    dbg = dbGlobals.DBGlobals()
    db = dbg.getDB()
    for doc in db.webpages.find():
        updatePage(doc, dbg)
