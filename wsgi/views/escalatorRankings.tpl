%# Get rankings for escalators
%from metroEscalatorsWeb import stationCodeToWebPath, escUnitIdToWebPath
%import metroTimes

%# Number to include in each report
%N=20
%
%#Unpack the keys for the rankings
%mostBreaks = rankings['mostBreaks']
%mostInspected = rankings['mostInspected']
%mostUnavailable = rankings['mostUnavailable']
%mostBrokenTimePercentage = rankings['mostBrokenTimePercentage']

<h2>Escalator Rankings</h2>
<div>
<table>
%timefmt = '%a, %m/%d/%y %H:%M'
%reportRangeSec = (rankings['reportEnd'] - rankings['reportStart']).total_seconds()
%reportRangeStr = metroTimes.secondsToDHM(reportRangeSec)
<tr><td>Report Start Time</td><td>{{rankings['reportStart'].strftime(timefmt)}}</td></tr>
<tr><td>Report End Time</td><td>{{rankings['reportEnd'].strftime(timefmt)}}</td></tr>
<tr><td>Report Time Range</td><td>{{reportRangeStr}}</td></tr>
</table>
</div>
  
<div>
<h3>Most Breaks</h3>
<p>The greatest number of breaks during the report time range.</p>
<table>
<tr>
    <th>Escalator</th>
    <th>Station</th>
    <th>Num. Breaks</th>
</tr>
%for rec in mostBreaks:
%   escalatorWebPath=escUnitIdToWebPath(rec['unitId'])
%   stationWebPath=stationCodeToWebPath(rec['stationCode'])
<tr>
    <td><a href="{{escalatorWebPath}}">{{rec['unitId']}}</a></td>
    <td><a href="{{stationWebPath}}">{{rec['stationName']}}</a></td>
    <td>{{str(rec['numBreaks'])}}</td>
</tr>
%end
</table>
</div>

<div>
<h3>Most Broken</h3>
<p>The fraction of time
that Metrorail is open for which the escalator is in a broken state.
Examples of broken states include CALLBACK/REPAIR, MAJOR REPAIR, etc.</p>
<table>
<tr>
    <th>Escalator</th>
    <th>Station</th>
    <th>Broken Time Percentage</th>
</tr>
%for rec in mostBrokenTimePercentage:
%   escalatorWebPath=escUnitIdToWebPath(rec['unitId'])
%   stationWebPath=stationCodeToWebPath(rec['stationCode'])
<tr>
    <td><a href="{{escalatorWebPath}}">{{rec['unitId']}}</a></td>
    <td><a href="{{stationWebPath}}">{{rec['stationName']}}</a></td>
    <td>{{'%.2f%%'%(100.0*rec['brokenTimePercentage'])}}</td>
</tr>
%end
</table>
</div>

<div>
<h3>Most Inspected</h3>
<p>The escalators with the greatest number of inspections during the report time range.</p>
<table>
<tr>
    <th>Escalator</th>
    <th>Station</th>
    <th>Num. Inspections</th>
</tr>
%for rec in mostInspected:
%   escalatorWebPath=escUnitIdToWebPath(rec['unitId'])
%   stationWebPath=stationCodeToWebPath(rec['stationCode'])
<tr>
    <td><a href="{{escalatorWebPath}}">{{rec['unitId']}}</a></td>
    <td><a href="{{stationWebPath}}">{{rec['stationName']}}</a></td>
    <td>{{str(rec['numInspections'])}}</td>
</tr>
%end
</table>
</div>

<div>
<h3>Most Unavailabile</h3>
<p>The escalators with the lowest availability
during the report time range. Availability is the 
percentage of time that Metrorail is open that the 
escalator is operating.</p>
<table>
<tr>
    <th>Escalator</th>
    <th>Station</th>
    <th>Availability</th>
</tr>
%for rec in mostUnavailable:
%   escalatorWebPath=escUnitIdToWebPath(rec['unitId'])
%   stationWebPath=stationCodeToWebPath(rec['stationCode'])
<tr>
    <td><a href="{{escalatorWebPath}}">{{rec['unitId']}}</a></td>
    <td><a href="{{stationWebPath}}">{{rec['stationName']}}</a></td>
    <td>{{'%.2f%%'%(100.0*rec['availability'])}}</td>
</tr>
%end
</table>
</div>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

%rebase layout title='DC Metro Metrics: Escalator Rankings'
