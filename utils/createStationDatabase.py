# Author: Lee Mendelowitz
# Date: 2/19/2013

# Create a database of stations: stations.py
# Write variables to a python module, which can be
# imported
#############################################
import json
from collections import defaultdict
import numpy as np
import sys, os

# Add parent dir to sys path
curfile = os.path.abspath(__file__)
curdir = os.path.split(curfile)[0]
parentdir = os.path.split(curdir)[0]
REPO_DIR = parentdir
sys.path.append(REPO_DIR)

import dcmetrometrics
from dcmetrometrics.eles.WMATA_API import WMATA_API
from dcmetrometrics.keys import WMATA_API_KEY

class StationEscalatorData(object):
    def __init__(self, codes, numEscalators, numRiders, weight):
        self.numEscalators = numEscalators
        self.numRiders = numRiders
        self.weight = weight
        self.codes = codes
        self.escalatorWeight = float(self.weight)/self.numEscalators if self.numEscalators > 0 else 0.0

    def makeDict(self):
        keys = ['numEscalators', 'numRiders', 'weight', 'codes', 'escalatorWeight']
        d = dict((k, self.__dict__[k]) for k in keys)
        return d

class Station(object):

    def __init__(self, apiDict):
        d = apiDict
        self.code = d['Code']
        self.name = d['Name']
        self.shortName = None # Set later
        self.lat = d['Lat']
        self.lon = d['Lon']

        lineCodeKeys = ['LineCode%i'%i for i in (1,2,3,4)]
        self.lineCodes = [c for c in (d.get(k, None) for k in lineCodeKeys) if c]

        sharedStationKeys = ['StationTogether%i'%i for i in (1,2)]
        self.sharedStations = [c for c in (d.get(k, None) for k in sharedStationKeys) if c]

        self.allCodes = [self.code] + self.sharedStations
        self.allLines = None # Set Later

    def addEscalatorData(self, data):
        for k,v in data.iteritems():
            setattr(self, k, v)

    def __getitem__(self, k):
        return getattr(self, k, None)

    def makeDict(self):
        return dict(self.__dict__)

#######################################
# Get the weight of each escalator,
# to compute weighted availability
def getStationEscalatorData():
    import os
    import pandas
    cwd = os.getcwd()
    dataFile = os.path.join(REPO_DIR,'data', 'stations.data.csv')
    stationData = pandas.read_table(dataFile)
    codes = stationData['Codes']
    riders = stationData['2012***']
    numEsc = stationData['N']
    stationsWithEsc = numEsc > 0
    stationsWithNoEsc = np.logical_not(stationsWithEsc)
    denom = float(riders[stationsWithEsc].sum())
    weight = riders/denom
    weight[stationsWithNoEsc] = 0.0

    stationCodeToData = {}
    for myCodes, myWeight, riderCount, escCount in zip(codes, weight, riders, numEsc):
        if pandas.isnull(myCodes):
            continue
        myCodes = myCodes.split(',')
        sd = StationEscalatorData(myCodes, escCount, riderCount, myWeight)
        for c in myCodes:
            stationCodeToData[c] = sd

    stationCodeToData = dict((k,v.makeDict()) for k,v in stationCodeToData.items())
    return stationCodeToData

###########################
# Read station names and short names from csv file
def getStationNames():
    import os
    import pandas
    cwd = os.getcwd()
    dataFile = os.path.join(REPO_DIR,'data', 'station.names.csv')
    stationData = pandas.read_table(dataFile, sep=',')
    codeToName = dict(zip(stationData['code'], stationData['long_name']))
    codeToShortName = dict(zip(stationData['code'], stationData['short_name']))
    return (codeToName, codeToShortName)


def defineVariables():

    api = WMATA_API(key=WMATA_API_KEY)

    allStations = json.loads(api.getStations().text)['Stations']
    allStations = [Station(data) for data in allStations]
    codeToStationData = dict((s.code, s) for s in allStations)

    codeToName, codeToShortName = getStationNames()

    # 7/26: Removing Escalator Data because it is missing for new Silver Line Stations
    # codeToEscalatorData = getStationEscalatorData()
    # assert(set(codeToName.keys()) == set(codeToEscalatorData.keys()) == set(codeToShortName.keys()))

    # Adjust the station names and add escalator data
    for code in codeToName.iterkeys():
        s = codeToStationData[code]
        s.name = codeToName[code]
        s.shortName = codeToShortName[code]
        #escD = codeToEscalatorData[code]
        #s.addEscalatorData(escD)

    # Set the allLines attribute for each station
    codeToAllLines = defaultdict(list)
    for s in allStations:
        for c in s.allCodes:
            codeToAllLines[c].extend(s.lineCodes)
    for c in codeToAllLines:
        allLines = list(set(codeToAllLines[c]))
        s = codeToStationData[c]
        s.allLines = allLines
   
    allCodes = [s.code for s in allStations]

    nameToCodes = defaultdict(list)
    for code,name in codeToName.iteritems():
        nameToCodes[name].append(code)
    nameToCodes = dict(nameToCodes)
    
    # Compile a list of station codes for each line
    lineToCodes = defaultdict(list)
    # Get Lines for a station
    def getLines(s):
        keys = ['LineCode%i'%i for i in range(1,5)]
        lines = [l for l in (s[k] for k in keys) if l is not None]
        return lines
    for s in allStations:
        lines = getLines(s)
        for l in lines:
            lineToCodes[l].append(s['Code'])
    lineToCodes = dict(lineToCodes)


    # Convert classes to dictionaries before exporting
    allStations = [s.makeDict() for s in allStations]
    codeToStationData = dict((k, s.makeDict()) for k,s in codeToStationData.iteritems())

    res = { 'allStations' : allStations,
            'codeToStationData' : codeToStationData,
            'codeToName' : codeToName,
            'codeToShortName' : codeToShortName,
            'nameToCodes': nameToCodes,
            'lineToCodes' : lineToCodes,
            'allCodes' : allCodes,
            #'codeToEscalatorData' : codeToEscalatorData
        }
    return res

def writeModule(moduleName, varDict):
    import pprint
    fout = open(moduleName, 'w')
    printer = pprint.PrettyPrinter()

    # Write variables
    for var,item in varDict.items():
        fout.write('%s = \\\n%s\n\n'%(var, printer.pformat(item)))

    fout.close()


def run():
    moduleName = 'stations2.py'
    varDict = defineVariables()
    writeModule(moduleName, varDict)

if __name__ == '__main__':
    run()
