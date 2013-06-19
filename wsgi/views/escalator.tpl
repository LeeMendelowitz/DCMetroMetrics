%# Listing for an escalator
%from metroEscalatorsWeb import stationCodeToWebPath
%from metroTimes import secondsToDHM, secondsToHMS
    
%#escalator data
<h2>Escalator {{unitId}}</h2>
<table class="escalator_data">
%stationWebPath = stationCodeToWebPath(escData['station_code'])
<tr> <td>Station Name</td><td><a href="{{stationWebPath}}">{{escData['station_name']}}</a></td></tr>
<tr> <td>Station Code</td><td>{{escData['station_code']}}</td> </tr>
<tr> <td>Station Description</td><td>{{escData['station_desc']}}</td></tr>
<tr> <td>Escalator Description</td><td>{{escData['esc_desc']}}</td></tr>
</table>

%#escalator summary
<h2>Summary</h2>
<table class="escalator_summary">
<tr> <td>Num. Breaks</td><td>{{escSummary['numBreaks']}}</td> </tr>
<tr> <td>Num. Fixes</td><td>{{escSummary['numFixes']}}</td> </tr>
<tr> <td>Num. Inspections</td><td>{{escSummary['numInspections']}}</td></tr>
<tr> <td>Availability</td><td>{{'%.3f%%'%(100.0*escSummary['availability'])}}</td></tr>
<tr> <td>Report Time Range</td><td>{{secondsToDHM(escSummary['absTime'])}}</td></tr>
%#<tr> <td>Report Metro Open Time</td><td>{{secondsToDHM(escSummary['metroOpenTime'])}}</td></tr>
</table>

<h2>History</h2>
<table class="status">
<tr>
    <th>Time</th>
    <th>Status</th>
    <th>Duration</th>
%#    <th>Tick Delta</th>
</tr>
%for status in statuses:
%   tf = '%a, %m/%d/%y %H:%M'
%   timeStr = status['time'].strftime(tf)
%   durationStr = ''
%   if 'end_time' in status:
%      duration = status['end_time'] - status['time']
%      durationStr = secondsToDHM(duration.total_seconds())
%   end
%   tickDeltaStr = secondsToHMS(status.get('tickDelta',0.0))
<tr class={{status['symptomCategory'].lower()}}>
    <td>{{timeStr}}</td>
    <td>{{status['symptom']}}</td>
    <td>{{durationStr}}</td>
%#    <td>{{tickDeltaStr}}</td>
</tr>
%end
</table>

%rebase layout title=unitId
