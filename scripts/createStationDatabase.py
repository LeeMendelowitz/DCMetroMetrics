# Author: Lee Mendelowitz
# Date: 2/19/2013

# Create a database of stations
# Write variables to a python module, which can be
# imported
#############################################

import wmataApi
import json
from collections import defaultdict
import renameStations
import numpy as np


class StationData(object):
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

#######################################
# Get the weight of each escalator,
# to compute weighted availability
def getStationData():
    import os
    import pandas
    cwd = os.getcwd()
    repo_root = os.path.split(cwd)[0]
    dataFile = os.path.join(repo_root,'data', 'stations.data.csv')
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
        sd = StationData(myCodes, escCount, riderCount, myWeight)
        for c in myCodes:
            stationCodeToData[c] = sd

    stationCodeToData = dict((k,v.makeDict()) for k,v in stationCodeToData.items())
    return stationCodeToData


def defineVariables():
    api = wmataApi.WMATA_API()
    allStations = json.loads(api.getStations().text)['Stations']

    codeToInfo = dict((sInfo['Code'], sInfo) for sInfo in allStations)
    codeToName = dict((sInfo['Code'], sInfo['Name']) for sInfo in allStations)
    codeToShortName = dict((k,renameStations.shortName(v)) for k,v in codeToName.items())
    allCodes = [s['Code'] for s in allStations]

    nameToCodes = defaultdict(list)
    for code,name in codeToName.iteritems():
        nameToCodes[name].append(code)
    nameToCodes = dict(nameToCodes)
    

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

    codeToData = getStationData()
    for c, d in codeToData.iteritems():
        d['name'] = codeToName[c]




    res = { 'allStations' : allStations,
            'codeToInfo' : codeToInfo,
            'codeToName' : codeToName,
            'codeToShortName' : codeToShortName,
            'nameToCodes': nameToCodes,
            'lineToCodes' : lineToCodes,
            'allCodes' : allCodes,
            'codeToData' : codeToData}
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
    moduleName = 'stations.py'
    varDict = defineVariables()
    writeModule(moduleName, varDict)

if __name__ == '__main__':
    run()
