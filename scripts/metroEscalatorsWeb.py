# Functions for the MetroEscalators website
import stations
import dbUtils
from StringIO import StringIO


PATHS = {'escalators' : '/escalators',
         'home' : '/',
         'stations' : '/stations',
         'hotcars' : '/hotcars'}

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
    return recs 

##########################################
# Generate the listing of all escalators
def escalatorList():
    nameToStationCode = stations.nameToCodes
    codeToStationData = stations.codeToStationData
    recs = []
    systemAvailability = dbUtils.getSystemAvailability()
    stationToAvailability = systemAvailability['stationToAvailability']
    numWorking = lambda sl: sum(1 for s in sl if s['symptomCategory']=='ON')

    curEscStatuses = systemAvailability['lastStatuses']

    escalatorListing = []
    for esc in curEscStatuses:
        unitId = esc['unit_id']
        shortUnitId = unitId[0:6]
        rec = { 'unitId' : shortUnitId,
                'stationName' : esc['station_name'],
                'stationDesc' : esc['station_desc'],
                'escDesc' : esc['esc_desc'],
                'symptom' : esc['symptom'],
                'symptomCategory' : esc['symptomCategory']
              }
        escalatorListing.append(rec)
    return escalatorListing


