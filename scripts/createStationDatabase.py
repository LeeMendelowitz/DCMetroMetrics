# Author: Lee Mendelowitz
# Date: 2/19/2013

# Create a database of stations
# Write variables to a python module, which can be
# imported
#############################################

import request
import json
from collections import defaultdict
import renameStations

def defineVariables():
    Req = request.Requester()
    allStations = json.loads(Req.getStations().text)['Stations']

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

    res = { 'allStations' : allStations,
            'codeToInfo' : codeToInfo,
            'codeToName' : codeToName,
            'codeToShortName' : codeToShortName,
            'nameToCodes': nameToCodes,
            'lineToCodes' : lineToCodes,
            'allCodes' : allCodes }
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
