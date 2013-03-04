import cPickle
import copy
import twitterApp
from datetime import datetime, time, date, timedelta

# Make a pickle file test1.pickle with some incidents
# This script will modify that data to create a second input pickle for the twitter app

pickle1 = 'test1.pickle'
pickle2 = 'test2.pickle' # To be created

data1 = cPickle.load(open(pickle1))
for inc in data1['incidents']:
    inc.UnitType = 'ESCALATOR'

data2 = copy.deepcopy(data1)

# Remove one incident, add a new incident, and change the status of an incident
inc = data2['incidents']
fixedUnitId = inc[-1].UnitId
fixedUnitTime = datetime.now() - timedelta(hours=2, minutes=10)
inc = inc[:-1] # Remove one

newIncident = copy.deepcopy(inc[-1])
newIncident.UnitName = 'MyUnit'
newIncident.UnitId = 'MyUnitEscalator'
newIncident.UnitType = 'ESCALATOR'
inc.append(newIncident)

newIncident = copy.deepcopy(newIncident)
newIncident.UnitName = 'BeingInspected'
newIncident.UnitId = 'MyInspectedUnit'
newIncident.SymptomDescription = 'PREV. MAINT. INSPECTION'
inc.append(newIncident)


# Change the status of the first incident
inc[0].SymptomDescription = 'SLIPPERY'
data2['incidents'] = inc

fout = open(pickle2, 'w')
cPickle.dump(data2, fout)
fout.close()

# Make a test State file
testStateFile = 'test.state'
s = twitterApp.State(pickle1, pickle2)
s.nextInspectionReportTime = datetime.combine(date=date.today(), time=time(hour=0))
s.unitIdToBrokeTime[fixedUnitId] = fixedUnitTime
s.numBreaks = 10
s.numFixes = 5
s.inspectedUnits = set(['ONE', 'TWO'])
s.write(testStateFile)

# Report the differences
T = twitterApp.TwitterApp(testStateFile, DEBUG=True)
T.reportDifferences(data1['incidents'], data2['incidents'])
T.processInspections(data2['incidents'])
T.state.write('test.after.state')


