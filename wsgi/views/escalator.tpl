%# Listing for an escalator

%from dcmetrometrics.web.eles import stationCodeToWebPath, symptomCategoryToClass
%from dcmetrometrics.common.metroTimes import secondsToDHM, secondsToHMS, toLocalTime

%description = "DC Metro Escalator {0} at {1} station, {2} {3}. Escalator performance history, and more."
%description = description.format(unitId, escData['station_name'], escData['station_desc'], escData['esc_desc'])
%#escalator data

<div class="container">
<div class="main-content">

<h2>Escalator {{unitId}}</h2>
<table class="escalator_data table table-bordered table-hover table-striped" style="min-width:250px; width:40%">
%stationWebPath = stationCodeToWebPath(escData['station_code'])
<tr> <td>Station Name</td><td><a href="{{stationWebPath}}">{{escData['station_name']}}</a></td></tr>
<tr> <td>Station Code</td><td>{{escData['station_code']}}</td> </tr>
<tr> <td>Station Description</td><td>{{escData['station_desc']}}</td></tr>
<tr> <td>Escalator Description</td><td>{{escData['esc_desc']}}</td></tr>
</table>

%#escalator summary
<h2>Summary</h2>
<table class="escalator_summary table table-bordered table-hover table-striped" style="min-width:250px; width:40%">
<tr> <td>Num. Breaks</td><td>{{escSummary['numBreaks']}}</td> </tr>
<tr> <td>Num. Fixes</td><td>{{escSummary['numFixes']}}</td> </tr>
<tr> <td>Num. Inspections</td><td>{{escSummary['numInspections']}}</td></tr>
<tr> <td>Availability</td><td>{{'%.3f%%'%(100.0*escSummary['availability'])}}</td></tr>
<tr> <td>Report Time Range</td><td>{{secondsToDHM(escSummary['absTime'])}}</td></tr>
%#<tr> <td>Report Metro Open Time</td><td>{{secondsToDHM(escSummary['metroOpenTime'])}}</td></tr>
</table>

<h2>History</h2>
<table class="status table table-hover">
<tr>
    <th>Time</th>
    <th>Status</th>
    <th>Duration</th>
%#    <th>Tick Delta</th>
</tr>
%for status in statuses:
%   tf = '%a, %m/%d/%y %I:%M %p'
%   localTime = toLocalTime(status['time'])
%   timeStr = localTime.strftime(tf)
%   durationStr = ''
%   if 'end_time' in status:
%      duration = status['end_time'] - status['time']
%      durationStr = secondsToDHM(duration.total_seconds())
%   end
%   tickDeltaStr = secondsToHMS(status.get('tickDelta',0.0))
%   symptomCat = status['symptomCategory'].lower()
<tr class={{symptomCategoryToClass[symptomCat]}}>
    <td>{{timeStr}}</td>
    <td>{{status['symptom']}}</td>
    <td>{{durationStr}}</td>
%#    <td>{{tickDeltaStr}}</td>
</tr>
%end
</table>

%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

</div>
</div>

%rebase layout title=unitId, description=description
