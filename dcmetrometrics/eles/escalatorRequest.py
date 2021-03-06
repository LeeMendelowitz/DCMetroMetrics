"""
eles.esclatorRequest

Get escalator incidents through the wmata API
"""

# Python modules
import time
import os
import sys
import cPickle
from collections import defaultdict, Counter
from datetime import datetime

# Custom modules
from ..common import stations
from ..keys import WMATA_API_KEY
from .WMATA_API import WMATA_API, WMATA_API_ERROR
from .Incident import Incident

api = None
def getAPI():
    global api
    if WMATA_API_KEY is None:
        return None
    if api is not None:
        return api
    api = WMATA_API(key=WMATA_API_KEY)
    return api

# Summarize results to standard output
def summarize(result):
    """
    Summarize the escalator/elevator statuses to standard output.
    """
    incidents = result['incidents']
    numIncidents = len(incidents)
    timeStr = time.strftime('%d_%b_%Y-%H_%M_%S', result['requestTime'])
    sys.stdout.write('Time: %s\n'%timeStr)

    sys.stdout.write('\n\n')
    sys.stdout.write('Num Incidents: %i\n'%numIncidents)

    symptomCounts = Counter(i['SymptomDescription'] for i in incidents)
    maxWidth = max(len(s) for s in symptomCounts.keys())
    formatStr = '{symptom:%is} {count:d}\n'%maxWidth
    for symptom, count in symptomCounts.most_common():
        outS = formatStr.format(symptom=symptom, count=count)
        sys.stdout.write(outS)
    sys.stdout.write('\n\n')

    # Gather incidents by station Code
    stationToIncident = defaultdict(list)
    for d in incidents:
        stationToIncident[d['StationCode']].append(d)
    for code in sorted(stations.allCodes):
        stationIncidents = stationToIncident.get(code, [])
        sys.stdout.write('%s (%s): %i\n'%(stations.codeToName[code], code, len(stationIncidents)))

def run():
    """
    Dump all incidents to a pickle file.
    """
    requestTime = time.localtime()
    timeStr = time.strftime('%d_%b_%Y-%H_%M_%S', requestTime)
    api = getAPI()
    res = api.getEscalator()
    incidents = res.json()['ElevatorIncidents']

    websiteTxt = Req.getEscalatorWebpageStatus().text

    result = { 'incidents' : incidents,
               'requestTime' : time.localtime(),
               'webpage' : websiteTxt }

    summarize(result) 

    fname = '%s.pickle'%(timeStr)
    fout = open(fname, 'w')
    cPickle.dump(result, fout)
    fout.close()

# Make a request for the twitter app

if __name__ == '__main__':
    run()
