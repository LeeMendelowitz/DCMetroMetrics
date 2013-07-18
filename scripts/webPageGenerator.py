# Greenlet to run the generation
# of web pages in the background.
import os
import sys
from datetime import datetime, timedelta
import gevent
import bottle
from operator import itemgetter
from collections import defaultdict, Counter
import __builtin__

import dbUtils
import stations
import metroEscalatorsWeb
import hotCarsWeb
import hotCars
from metroTimes import utcnow, toLocalTime, localToUTCTime, tzutc
from restartingGreenlet import RestartingGreenlet

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
    __builtin__.reload(metroEscalatorsWeb)
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
def initDB():
    db = dbUtils.getDB()

    queries = []

    # The home page
    queries.append({'class' : 'home'})

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

    # The glossary
    queries.append({'class' : 'glossary'})

    # The Data downloads page
    queries.append({'class' : 'data'})

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
def genEscalatorPage(doc):
    escId = doc['escalator_id']
    escUnitName = dbUtils.escIdToUnit[escId]
    escUnitShort = escUnitName[0:6]
    db = dbUtils.getDB()
    if escId is None:
        return 'No escalator found'
    statuses = dbUtils.getEscalatorStatuses(escId = escId)
    dbUtils.addStatusAttr(statuses)

    curTime = utcnow()
    # Set the end_time of the current status to now
    if statuses and 'end_time' not in statuses[0]:
        statuses[0]['end_time'] = curTime

    escData = dbUtils.escIdToEscData[escId]

    # Summarize the escalator performance
    startTime =  statuses[-1]['time'] if statuses else localToUTCTime(datetime(2000,1,1))
    escSummary = dbUtils.summarizeStatuses(statuses, startTime=startTime, endTime=curTime)

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
def genEscalatorRankings_Old(doc):
    rankingDict = metroEscalatorsWeb.getRankings()
    compiledRankings = metroEscalatorsWeb.compileRankings(rankingDict)
    stationCodeToSummary = metroEscalatorsWeb.getStationSummaries()
    dtStationRankings = metroEscalatorsWeb.makeStationRankingGoogleTable(stationCodeToSummary)
    content = makePage('escalatorRankings', rankings=compiledRankings, dtStationRankings=dtStationRankings)
    filename = 'escalatorRankings.html'
    writeContent(filename, content)

###################################
def genEscalatorRankings(doc):
    now = utcnow()
    rankingArgs = [
                     #key,  (startTime, endTime),       header value
                    ('d1', (now - timedelta(days=1), now), '1 day'),
                    ('d3', (now - timedelta(days=3), now), '3 day'),
                    ('d7', (now - timedelta(days=7), now), '7 day'),
                    ('d14', (now - timedelta(days=14), now), '14 day'),
                    ('d28', (now - timedelta(days=28), now), '28 day'),
                    ('AllTime', (None, None), 'All Time') ]
    def makeEntry(args, header):
        dt = metroEscalatorsWeb.escalatorRankingsTable(*args)
        return {'dataTable' : dt,
                'json' : dt.ToJSon(),
                'header' : header}

    rankingsDict = dict((k, makeEntry(args, header)) for k,args,header in rankingArgs)
    dtDailyCounts = metroEscalatorsWeb.makeBreakInspectionTable()
    stationCodeToSummary = metroEscalatorsWeb.getStationSummaries()
    dtStationRankings = metroEscalatorsWeb.makeStationRankingGoogleTable(stationCodeToSummary)

    # Write html
    content = makePage('escalatorRankings', rankingsDict = rankingsDict, dtDailyCounts=dtDailyCounts, dtStationRankings=dtStationRankings)
    filename = 'escalatorRankings.html'
    writeContent(filename, content)

    # Write javacsript
    content = makePage('escalatorRankings_js', rankingsDict=rankingsDict, dtDailyCounts=dtDailyCounts, dtStationRankings=dtStationRankings)
    filename = 'escalatorRankings.js'
    writeContent(filename, content)

#########
def genHomePage(doc):
    content = makePage('home')
    filename = 'home.html'
    writeContent(filename, content)

#########
def genDataPage(doc):
    content = makePage('data')
    filename = 'data.html'
    writeContent(filename, content)

#####################################################
# Generate the escalator outages page.
# Doc is the record for this page in the db.webpages collection.
def genEscalatorOutages(doc):
    escalatorList = metroEscalatorsWeb.escalatorNotOperatingList()

    # Summarize the non-operational escalators by symptom
    symptomCounts = Counter(esc['symptom'] for esc in escalatorList)

    # Generate the data for the Google Chart pi chart
    import gviz_api

    # Get data for the Outage Categories summary
    schema = [('symptom', 'string', 'Outage Symptom' ), ('count', 'number', 'Count')]
    data = symptomCounts.items()
    dtSymptoms = gviz_api.DataTable(schema, data=data)

    # Convert the unitId and stationName into html links
    for d in escalatorList:
        d['unitIdHtml'] = metroEscalatorsWeb.makeEscalatorLink(d['unitId'])
        d['stationNameHtml'] = metroEscalatorsWeb.makeStationLink(d['stationCode'])
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
        return metroEscalatorsWeb.symptomCategoryToClass[sympCat] 
    dtOutagesRowClasses = [getOutageClass(d) for d in escalatorList]


    # Get the availability and weighted availability
    systemAvailability = dbUtils.getSystemAvailability()
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
    stationRecs, dtStations = metroEscalatorsWeb.stationList()

    # Make HTML
    content = makePage('stations', stationRecs=stationRecs, dtStations = dtStations)
    filename = 'stations.html'
    writeContent(filename, content)

    # Make javascript
    content = makePage('stations_js', stationRecs=stationRecs, dtStations = dtStations)
    filename = 'stations.js'
    writeContent(filename, content)

#########
def genHotCars(doc):

    hotCarData = hotCarsWeb.getAllHotCarData()
    dtHotCars = hotCarsWeb.hotCarGoogleTable(hotCarData)
    dtHotCarsByUser = hotCarsWeb.hotCarByUserGoogleTable()
    allReports = [r for d in hotCarData.itervalues() for r in d['reports']]
    summary = hotCars.summarizeReports(allReports)
    dtHotCarsBySeries = hotCarsWeb.makeCarSeriesGoogleTable(summary['seriesToCount'])
    dtHotCarsByColorCustom = hotCarsWeb.makeColorCountsGoogleTableCustom(summary['colorToCount'])
    dtHotCarsByColor = hotCarsWeb.makeColorCountsGoogleTable(summary['colorToCount'])
    dtHotCarsTimeSeries = hotCarsWeb.makeReportTimeSeries()
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

def genGlossaryPage(doc):
    content = makePage('glossary')
    filename = 'glossary.html'
    writeContent(filename, content)

def genHotCarPage(doc):
    carNum = doc['car_number']
    data = hotCarsWeb.getHotCarData(carNum)
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
           updatePage(doc, curTimeLocal, self.logFile)
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
      'stationDirectory' : genStationDirectory,
      'station' : genStationPage,
      'hotcars' : genHotCars,
      'hotcar' : genHotCarPage,
      'glossary' : genGlossaryPage,
      'data' : genDataPage,
      'home' : genHomePage
    }

############################################
def updatePage(doc, curTimeLocal = None, logFile = sys.stdout):
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
    pageGenerator(doc)
