# Functions for the MetroEscalators website
import stations
import dbUtils
from dbUtils import StatusGroup
from StringIO import StringIO
from operator import itemgetter
from datetime import datetime, date, timedelta
from collections import defaultdict
import gviz_api
import gevent

PATHS = {'escalators' : '/escalators/directory',
         'home' : '/',
         'stations' : '/stations',
         'hotcars' : '/hotcars',
         'escalatorOutages' : '/escalators/outages',
         'rankings' : '/escalators/rankings'
        }

###################################
# This can convert a list of codes or upper case words
# ex: lineCodes = ['RD', 'OR']
# or lineCodes = ['RED', 'ORANGE']
def lineToColoredSquares(lineCodes):
    codeToColor = {'RD' :'red',
                   'BL' :'blue',
                   'OR' :'orange',
                   'GR' :'green',
                   'YL' : 'yellow'}

    colors = codeToColor.values()
    wordToColor = dict(codeToColor)
    for c in colors:
        wordToColor[c.upper()] = c

    s = StringIO()
    colors = [wordToColor[lc] for lc in lineCodes]
    s.write('<div class="color_squares">')
    if colors:
        for color in colors:
            s.write('<div id="%ssquare"></div>'%(color))
    else:
        s.write('N/A')
    outS = s.getvalue()
    s.write('</div>')
    s.close()
    return outS

########################################
# Generate the web path for a station
# from its code
def stationCodeToWebPath(code):
   stationData = stations.codeToStationData[code]
   shortName = stationData['shortName']
   return '/stations/%s'%shortName


########################################
# Generate the web path for an escalator
# from its code
def escUnitIdToWebPath(unitId):
   unitId = unitId[0:6]
   return '/escalators/%s'%unitId

def escUnitIdToAbsWebPath(unitId):
    pfx = 'http://www.dcmetrometrics.com%s'%(escUnitIdToWebPath(unitId))
    return pfx

########################################
# Make a link to the station
def makeStationLink(code):
   webPath = stationCodeToWebPath(code) 
   stationData = stations.codeToStationData[code]
   stationName = stationData['name']
   html = '<a href="{path}">{name}</a>'.format(path=webPath, name=stationName)
   return html

########################################
# Make a link to the escalator
def makeEscalatorLink(unitId):
   unitId = unitId[0:6]
   webPath = escUnitIdToWebPath(unitId)
   html = '<a href="{path}">{name}</a>'.format(path=webPath, name=unitId)
   return html

########################################
# Generate the data for the listing of
# all stations
def stationList():
    nameToStationCode = stations.nameToCodes
    codeToStationData = stations.codeToStationData

    recs = []

    systemAvailability = dbUtils.getSystemAvailability()
    stationToAvailability = systemAvailability['stationToAvailability']
    stationToStatuses = systemAvailability['stationToStatuses']
    numWorking = lambda sl: sum(1 for s in sl if s['symptomCategory']=='ON')
    stationToNumWorking = dict((c,numWorking(sl)) for c,sl in stationToStatuses.iteritems())

    # Gather the station data
    for name, codes in nameToStationCode.iteritems():
        code = codes[0]
        stationData = codeToStationData[code]
        rec = { 'name' : stationData['name'],
                'codes' : stationData['allCodes'],
                'lines' : stationData['allLines'],
                'numEscalators' : stationData['numEscalators'],
                'numWorking' : stationToNumWorking[code],
                'availability' : stationToAvailability[code]}
        recs.append(rec)

    # Create a google DataTable with this information
    schema = [('name', 'string', 'Name'),
              ('codes', 'string', 'Code'),
              ('lines', 'string', 'Lines'),
              ('numEsc', 'number', 'Num. Escalators'),
              ('availability', 'number', 'Availability')]
    rows = []
    for rec in recs:
        stationCode = rec['codes'][0]
        codeStr = ', '.join(rec['codes'])
        row = [makeStationLink(stationCode),
               codeStr,
               lineToColoredSquares(rec['lines']),
               rec['numEscalators'],
               100.0*rec['availability']]
        rows.append(row)
    dtStations = gviz_api.DataTable(schema, rows)
    return (recs, dtStations)

##########################################
# Generate the listing of all escalators
def escalatorList():
    nameToStationCode = stations.nameToCodes
    codeToStationData = stations.codeToStationData
    recs = []
    systemAvailability = dbUtils.getSystemAvailability()
    numWorking = lambda sl: sum(1 for s in sl if s['symptomCategory']=='ON')

    curEscStatuses = systemAvailability['lastStatuses']

    escalatorListing = []
    for esc in curEscStatuses:
        unitId = esc['unit_id']
        shortUnitId = unitId[0:6]
        stationCode = esc['station_code']
        stationName = stations.codeToName[stationCode]
        rec = { 'unitId' : shortUnitId,
                'stationCode' : stationCode,
                'stationName' : stationName,
                'stationDesc' : esc['station_desc'],
                'escDesc' : esc['esc_desc'],
                'symptom' : esc['symptom'],
                'symptomCategory' : esc['symptomCategory'],
                'time' : esc['time']
              }
        escalatorListing.append(rec)
    return escalatorListing

#########################################################
# Generate a listing of escalators which are not working
def escalatorNotOperatingList():
    escList = escalatorList()
    notOperating = [esc for esc in escList if esc['symptomCategory'] != 'ON']

    # Sort not operating escalators by station name
    notOperating = sorted(notOperating, key = itemgetter('stationName'))
    return notOperating

#########################################################
def getRankings(startTime=None, endTime=None):

    if endTime is None:
        endTime = datetime.now()
    escToSummary = dbUtils.getAllEscalatorSummaries(startTime=startTime, endTime=endTime)

    # Add to the summary the percentage of Metro Open time that the escalator is broken
    for escId, escSum in escToSummary.iteritems():
        brokenTime= escSum['symptomCategoryToTime']['BROKEN']        
        escSum['brokenTimePercentage'] = float(brokenTime)/escSum['metroOpenTime']

    def keySort(q):
        def key(k):
            return escToSummary[k][q]
        return key 

    escIds = escToSummary.keys()
    mostBreaks = sorted(escIds, key = keySort('numBreaks'), reverse=True)
    mostInspected = sorted(escIds, key = keySort('numInspections'), reverse=True)
    mostUnavailable = sorted(escIds, key = keySort('availability'))
    mostBrokenTimePercentage = sorted(escIds, key = keySort('brokenTimePercentage'), reverse=True)

    reportStart = startTime
    if reportStart is None:
        reportStart = min(s['time'] for summary in escToSummary.itervalues() \
                              for s in summary['statuses'])
    reportEnd = endTime

    ret = { 'escToSummary' : escToSummary,
            'mostBreaks' : mostBreaks,
            'mostInspected' : mostInspected,
            'mostUnavailable' : mostUnavailable,
            'mostBrokenTimePercentage' : mostBrokenTimePercentage,
            'reportStart' : reportStart,
            'reportEnd' : reportEnd}

    return ret

#############################################################
# Sift through the rankings returned by getRankings and prepare
# data for HTML display
def compileRankings(rankingDict, N=20):
    escToSummary = rankingDict['escToSummary']

    reportTime = max(s['absTime'] for s in escToSummary.itervalues())
    mostBreaks = rankingDict['mostBreaks']
    mostInspected = rankingDict['mostInspected']
    mostUnavailable = rankingDict['mostUnavailable']
    mostBrokenTimePercentage = rankingDict['mostBrokenTimePercentage']

    def makeRecord(escId, key):
        unitId = dbUtils.escIdToUnit[escId][0:6]
        escData = dbUtils.escIdToEscData[escId]
        escSummary = escToSummary[escId]
        stationCode = escData['station_code']
        stationName = stations.codeToName[stationCode]
        rec = { 'unitId' : unitId,
                'stationCode' : stationCode,
                'stationName' : stationName,
                key : escSummary[key]}
        return rec

    mostBrokenData = [makeRecord(escId, 'numBreaks') for escId in mostBreaks[:N]]
    mostInspectedData = [makeRecord(escId, 'numInspections') for escId in mostInspected[:N]]
    mostUnavailableData = [makeRecord(escId, 'availability') for escId in mostUnavailable[:N]]
    mostBrokenTimePercentage = [makeRecord(escId, 'brokenTimePercentage') for escId in mostBrokenTimePercentage[:N]]

    ret =  {'mostBreaks' : mostBrokenData,
            'mostInspected' : mostInspectedData,
            'mostUnavailable' : mostUnavailableData,
            'mostBrokenTimePercentage' : mostBrokenTimePercentage,
            'reportStart' : rankingDict['reportStart'],
            'reportEnd' : rankingDict['reportEnd']
           }
    return ret
   

#########################################
# Make a Google Table of escalator rankings
def escalatorRankingsTable():
    rankingD = getRankings()
    escToSummary = rankingD['escToSummary']

    schema = [('unitId', 'string','Escalator'),
              ('station', 'string', 'Station'),
              ('breaks', 'number', 'Breaks'),
              ('inspections', 'number', 'Inspections'),
              ('availability', 'number','Availability'),
              ('broken', 'number', 'Broken Time')]
    
    rows = []
    for escId, summaryD in escToSummary.iteritems():
        escData = dbUtils.escIdToEscData[escId]
        stationCode = escData['station_code']
        escLink = makeEscalatorLink(escData['unit_id'])
        row = [escLink, makeStationLink(stationCode),
               summaryD['numBreaks'],
               summaryD['numInspections'],
               100.0*summaryD['availability'],
               100.0*summaryD['brokenTimePercentage']]
        rows.append(row)

    dtEscStats = gviz_api.DataTable(schema, rows)
    return dtEscStats

#########################################
# Make a plot of break counts and inspection counts
# per day
def makeBreakInspectionTable():
    escIds = dbUtils.escIdToUnit.keys()
    escToStatuses = {}
    getEscalatorStatuses = dbUtils.getEscalatorStatuses
    for escId in escIds:
        gevent.sleep(0.0)
        statuses = getEscalatorStatuses(escId=escId)[::-1] # Put in ascending order
        statusGroup = StatusGroup(statuses)
        breaks = statusGroup.breakStatuses()
        inspections = statusGroup.inspectionStatuses()
        d = {'breaks' : breaks,
             'inspections' : inspections}
        escToStatuses[escId] = d
    allBreaks = [b for d in escToStatuses.itervalues() for b in d['breaks']]
    allInspections = [i for d in escToStatuses.itervalues() for i in d['inspections']]
    allStatuses = allBreaks + allInspections
    
    # Group statuses by date 
    dayToInspections = defaultdict(list)
    dayToBreaks = defaultdict(list)
    minTime = min(s['time'] for s in allStatuses)
    firstDay = minTime.date()
    today = date.today()

    for b in allBreaks:
        day = b['time'].date()
        dayToBreaks[day].append(b)
    for i in allInspections:
        day = i['time'].date()
        dayToInspections[day].append(i)

    numDays = (today - firstDay).days
    days = [firstDay + timedelta(days=i) for i in range(numDays+1)]
    numBreaks = [len(dayToBreaks.get(day, [])) for day in days]
    numInspections = [len(dayToInspections.get(day, [])) for day in days]

    dayToOutages = getDataOutages()
    def makeOutageStr(d):
        outage = dayToOutages.get(d, None)
        if not outage:
            return None
        hours = int(outage/3600.0 + 0.5)
        return '%i hours'%hours

    outageLongAnnotations = [makeOutageStr(d) for d in days]
    outageShortAnnotations = ['Data Outage' if a is not None else None for a in outageLongAnnotations]


    schema = [('day', 'date', 'Day'),
              ('breaks', 'number','Breaks'),
              ('shortAnnotation', 'string', 'ShortAnnotation'),
              ('longAnnotation', 'string', 'LongAnnotation'),
              ('inspections', 'number','Inpsections'),
              #('shortAnnotation', 'string', 'ShortAnnotation'),
              #('longAnnotation', 'string','LongAnnotattion')
              ]
    sa = outageShortAnnotations
    la = outageLongAnnotations
    rows = zip(days, numBreaks, sa, la, numInspections) 
    dtBreakInspectionCounts = gviz_api.DataTable(schema, rows)
    return dtBreakInspectionCounts


###################################
# Find data outages 
# Just report the largest outage for a given day
def getDataOutages():
    db = dbUtils.getDB()
    allStat = list(db.escalator_statuses.find())
    T = 60*60
    delayed = [s for s in allStat if s['tickDelta'] >= T]

    dayToDelayed = defaultdict(list)
    for d in delayed:
        dayToDelayed[d['time'].date()].append(d)

    dayToOutage = {}
    for day,delayed in dayToDelayed.iteritems():
        maxDelay = max(d['tickDelta'] for d in delayed)
        dayToOutage[day] = maxDelay
    return dayToOutage

#####################################
def getStationSummaries():
    nameToStationCodes = stations.nameToCodes
    codeToStationData = stations.codeToStationData
    stationCodes = [codes[0] for codes in nameToStationCodes.itervalues()]

    # Only include stations with escalator
    stationCodes = [c for c in stationCodes if codeToStationData[c]['numEscalators'] > 0]

    stationCodeToSummary = {}

    for sc in stationCodes:
        summary = dbUtils.getStationSummary(sc)
        stationData = codeToStationData[sc]
        stationName = stationData['name']
        summary['stationName'] = stationName

        # Compute the broken time percentage
        brokenTime = summary['symptomCategoryToTime'].get('BROKEN', 0.0)
        metroOpenTime = summary['metroOpenTime']
        brokenTimePercentage = brokenTime/metroOpenTime if metroOpenTime > 0 else 0.0
        summary['brokenTimePercentage'] = brokenTimePercentage

        stationCodeToSummary[sc] = summary
    return stationCodeToSummary 

####################################
def makeStationRankingGoogleTable(stationCodeToSummary):

    schema = [('station', 'string', 'Station'),
              ('Num. Escalators', 'number', 'Num. Escalators'),
              ('Breaks', 'number', 'Breaks'),
              ('Inspections', 'number', 'Inspections'),
              ('Avg. Availability', 'number', 'Avg. Availability'),
              ('Broken Time', 'number', 'Broken Time')]


    rows = []
    for sc, data in stationCodeToSummary.iteritems():
        station = data['stationName']
        numEsc = len(data['escUnitIds'])
        row = [makeStationLink(sc),
               numEsc,
               data['numBreaks'],
               data['numInspections'],
               100.0*data['availability'],
               100.0*data['brokenTimePercentage']]
        rows.append(row)
    dtStationRankings = gviz_api.DataTable(schema, rows)
    return dtStationRankings 
