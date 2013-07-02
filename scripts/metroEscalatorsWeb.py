# Functions for the MetroEscalators website
import stations
import dbUtils
from StringIO import StringIO
from operator import itemgetter
from datetime import datetime
import gviz_api


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
    for color in colors:
        s.write('<div id="%ssquare"></div>'%(color))
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
   return '/escalators/%s'%unitId

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
              ('outages', 'number', 'Outages'),
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
          
