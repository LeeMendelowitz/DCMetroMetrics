import cPickle
import glob
from collections import defaultdict

def getAllIncidents():
    files = glob.glob('*.pickle')
    print '%i pickle files'%len(files)
    incidents = []
    for f in files:
        res = cPickle.load(open(f))
        incidents.extend(res['incidents'])
    return incidents

def splitUnitId(unitId):
    unitName = unitId[0:6]
    unitType = unitId[6:]
    assert(unitType in ('ESCALATOR', 'ELEVATOR'))
    return (unitName, unitType)

def getUnitName(unitId):
    unitName, unitType = splitUnitId(unitId)
    return unitName

def getUnitType(unitId):
    unitName, unitType = splitUnitId(unitId)
    return unitType

def parseUnits(incidents):
    unitDict = defaultdict(set)
    for i in incidents:
        myId = i['UnitName'] + i['UnitType']
        sn = i['StationName']
        loc = i['LocationDescription']
        unitDict[myId].add((sn,loc))

    for k,v in unitDict.iteritems():
        if len(v) > 1:
            raise RuntimeError('%s has more than one description! %s'%(k, str(v)))

    def makeD(info):
        sn, desc = info
        return {'station' : sn,
                'desc' : desc}
    unitDict = dict((k,makeD(iter(v).next())) for k,v in unitDict.iteritems())
    return unitDict

def writeUnitsFile(unitDict, fname = 'units.tsv'):
    items = []
    for u, info in unitDict.iteritems():
        sn = info['station']
        desc = info['desc']
        info2 = dict(info)
        info2['unit'] = u
        items.append(info2)

    # Sort the units by station, secondly by id
    items = sorted(items, key = lambda d: d['unit'])
    items = sorted(items, key = lambda d: d['station'])

    fout = open(fname, 'w')
    for rec in items:
        outS = '{d[station]}\t{d[unit]}\t{d[desc]}\n'.format(d=rec)
        fout.write(outS)
    fout.close()


def parseCodes(incidents, fname='codes.tsv'):
    info = ((i['SymptomCode'], i['SymptomDescription']) for i in incidents)
    infoSet = set(info)
    fout = open(fname, 'w')
    for code, desc in infoSet:
        outS = '{code}\t{desc}\n'.format(code=code, desc=desc)
        fout.write(outS)
    fout.close()
    return infoSet

def run():
    incidents = getAllIncidents()
    unitDict = parseUnits(incidents)
    writeUnitsFile(unitDict)
    symptomSet = parseCodes(incidents)

    return { 'incidents' : incidents,
             'unitDict' : unitDict,
             'symptomSet' : symptomSet }


if __name__ == '__main__':
    run()
