# Functions to help manually add a line color to hot car
# reports which are missing a line color:

# dumpCSV: Dump a CSV file with hot car reports which are missing line color
# addColorsFromCSV: Read in colors from a csv file.
# genUpdateScript: Generate a python script to update the MongoDB hotcars collection
#####################################################
#from . import test.test_setup
from . import dbUtils
from . import hotCars

import pandas
import bson
from StringIO import StringIO

db = dbUtils.getDB()

def dumpCSV(fname = 'hotcars.colormissing.csv'):
    hotCarDict = hotCars.getAllHotCarReports(db)
    allReports = [v for vl in hotCarDict.values() for v in vl]
    missingColor = [h for h in allReports if h['color']=='NONE']
    print '%i reports are missing color'%len(missingColor)

    myFields = ['_id', 'text', 'color']
    data = []
    for h in missingColor:
        d = dict((k,h[k]) for k in myFields)
        d['_id'] = str(d['_id'])
        d['text'] = d['text'].encode('ascii', errors='ignore').replace(',',' ')
        data.append(d)
    dt = pandas.DataFrame(data)
    dt.to_csv(fname,index=False)

def addColorsFromCSV(fname):
    dt = pandas.read_csv(fname)
    numRec = len(dt)
    colorInd = dt['color'] != 'NONE'
    colorDt = dt[colorInd]
    numColor = len(colorDt)
    print 'Found %i records out of %i with color'%(numColor, numRec)
    for recId, d in colorDt.iterrows():
        myId = d['_id']
        color = d['color']
        print myId, color
        myId = bson.objectid.ObjectId(myId)
        db.hotcars.update({"_id" : myId}, {"$set" : {"color" : color}})

script =\
"""\
#!/usr/bin/env python
import bson, os, sys

if "OPENSHIFT_MONGODB_DB_HOST" not in os.environ:
    print "Seems like this is not the OPENSHIFT environment. Importing test_setup."
    import test_setup

import dbUtils
db = dbUtils.getDB()

{cmds}

"""


def genUpdateScript(csvname, output='updateDBWithColors.py'):
    dt = pandas.read_csv(csvname)
    numRec = len(dt)
    colorInd = dt['color'] != 'NONE'
    colorDt = dt[colorInd]
    numColor = len(colorDt)
    print 'Found %i records out of %i with color'%(numColor, numRec)
    cmds = StringIO()
    for recId, d in colorDt.iterrows():
        myId = d['_id']
        color = d['color']
        print myId, color
        cmd = 'db.hotcars.update({{"_id" : bson.objectid.ObjectId("{0}")}}, {{"$set" : {{"color" : "{1}"}}}})'.format(myId,color)
        cmds.write(cmd + "\n")
    myScript = script.format(cmds=cmds.getvalue())
    cmds.close()
    fout = open(output, 'w')
    fout.write(myScript)
