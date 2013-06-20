# Greenlet to run the generation
# of web pages in the background.
import os
from datetime import datetime, timedelta
from gevent import Greenlet
import gevent
import bottle
from operator import itemgetter
from collections import defaultdict, Counter

import dbUtils
import stations
import metroEscalatorsWeb
import hotCarsWeb

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

##############################
# Make a wrapper around the bottle.template call
def makePage(*args, **kwargs):
    curTime = datetime.now()
    kwargs['curTime'] = curTime
    return bottle.template(*args, **kwargs)

###################################################
# Initialize the webpages collection in the database
def initDB():
    db = dbUtils.getDB()

    queries = []
    # All escalators get a page.
    escIds = dbUtils.escIdToUnit.keys()
    for escId in escIds:
        queries.append({'class' : 'escalator', 'escalator_id' : escId})

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

    # The non-operational listing gets a page
    queries.append({'class' : 'escalatorOutages'})

    # The hotcars page
    queries.append({'class' : 'hotcars'})

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
def genEscalatorPage(doc):
    escId = doc['escalator_id']
    escUnitName = dbUtils.escIdToUnit[escId]
    escUnitShort = escUnitName[0:6]
    db = dbUtils.getDB()
    if escId is None:
        return 'No escalator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId)
    dbUtils.addStatusAttr(statuses)

    curTime = datetime.now()
    # Set the end_time of the current status to now
    if statuses and 'end_time' not in statuses[0]:
        statuses[0]['end_time'] = curTime

    escData = dbUtils.escIdToEscData[escId]

    # Summarize the escalator performance
    startTime = datetime(2000,1,1)
    escSummary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=datetime.now())

    # Generate the page
    content = makePage('escalator', unitId = escUnitShort, escData=escData, statuses=statuses, escSummary=escSummary)
    filename = 'escalator_%s.html'%(escUnitShort)
    writeContent(filename, content)


#########
def genStationPage(doc):
    # Get the station code
    shortName = doc['station_name']
    codes = [c for c,sn in stations.codeToShortName.iteritems() if sn==shortName]
    if not codes:
        return 'No station found'
    stationCode = codes[0]

    # Get the summary for this station over all time
    stationSummary = dbUtils.getStationSummary(stationCode)

    # Get the current overview of escalators in this station
    stationSnapshot = dbUtils.getStationSnapshot(stationCode)
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
        escId = dbUtils.unitToEscId[escUnitId]
        escMetaData = dbUtils.escIdToEscData[escId]
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
def genEscalatorRankings(doc):
    rankingDict = metroEscalatorsWeb.getRankings()
    compiledRankings = metroEscalatorsWeb.compileRankings(rankingDict)
    content = makePage('escalatorRankings', rankings=compiledRankings)
    filename = 'escalatorRankings.html'
    writeContent(filename, content)

#########
def genEscalatorOutages(doc):
    escalatorList = metroEscalatorsWeb.escalatorNotOperatingList()

    # Summarize the non-operational escalators by symptom
    symptomCounts = Counter(esc['symptom'] for esc in escalatorList)

    # Get the availability and weighted availability
    systemAvailability = dbUtils.getSystemAvailability()
    content = makePage('escalatorOutages', escList=escalatorList, symptomCounts=symptomCounts, systemAvailability=systemAvailability)
    filename = 'escalatorOutages.html'
    writeContent(filename, content)

#########
def genEscalatorDirectory(doc):
    escalatorList = metroEscalatorsWeb.escalatorList()

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
def genStationDirectory(doc):
    stationRecs = metroEscalatorsWeb.stationList()
    content = makePage('stations', stationRecs=stationRecs)
    filename = 'stations.html'
    writeContent(filename, content)

#########
def genHotCars(doc):
    hotCarData = hotCarsWeb.getHotCarData()
    content = makePage('hotCars', hotCarData=hotCarData)
    filename = 'hotcars.html'
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
        fout.write(content)
##################################################################

class WebPageGenerator(Greenlet):

    def __init__(self, SLEEP=10):
        Greenlet.__init__(self)
        self.SLEEP = SLEEP
        self.logFileName = os.path.join(DATA_DIR, 'webPageGenerator.log')
        self.logFile = None

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
        db = dbUtils.getDB()
        initDB() # Add any missing documents to the database
       
        # Get documents that need to be updated 
        docs = list(db.webpages.find({'forceUpdate' : True}))

        # Get documents with no lastUpdateTime field
        docs.extend(db.webpages.find({'lastUpdateTime' : {'$exists' : False}}))

        # Get stale documents
        curTime = datetime.now()
        oneHourAgo = curTime - timedelta(hours=1)
        docs.extend(db.webpages.find({'lastUpdateTime' : {'$lt' : oneHourAgo}}))

        # Make the document list unique
        seen = set()
        docs = [d for d in docs if not (d['_id'] in seen or seen.add(d['_id']))]

        # Make the updates
        classToPageGenerator =  \
            { 'escalator' : genEscalatorPage,
              'escalatorRankings' : genEscalatorRankings,
              'escalatorDirectory': genEscalatorDirectory,
              'escalatorOutages' : genEscalatorOutages,
              'stationDirectory' : genStationDirectory,
              'station' : genStationPage,
              'hotcars' : genHotCars
            }
        
        for doc in docs:
           # Get the webpage generator based on the doc's class
           pageGenerator = classToPageGenerator.get(doc['class'], None)
           if pageGenerator is None:
               raise RuntimeError('No page generator for webpage with class %s'%doc['class'])

           #Generate the webpage
           tf = '%m/%d/%y %H:%M'
           timeStamp = datetime.now().strftime(tf)
           self.logFile.write("%s: Updating webpage: %s\n"%(timeStamp,str(doc)))
           pageGenerator(doc)

           #Update the webpage database
           newDoc = dict(doc)
           newDoc['lastUpdateTime'] = datetime.now()
           newDoc['forceUpdate'] = False
           db.webpages.update({'_id' : doc['_id']}, newDoc)
