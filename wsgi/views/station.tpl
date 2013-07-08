%# Page for a station
%import metroEscalatorsWeb
%from metroEscalatorsWeb import lineToColoredSquares, escUnitIdToWebPath
    
%#station data
%codeStr = ', '.join(stationSnapshot['allCodes'])
%lineStr = lineToColoredSquares(stationSnapshot['lineCodes'])
%numRiderStr = '{:,d}'.format(stationSnapshot['numRiders'])

<h2>{{stationSnapshot['name']}}</h2>

<h3>Station Data</h3>
<table class="station_data">
<tr> <td>Station Name</td><td>{{stationSnapshot['name']}}</td> </tr>
<tr> <td>Station Codes</td><td>{{codeStr}}</td> </tr>
<tr> <td>Station Lines</td><td>{{!lineStr}} </td></tr>
<tr> <td>Avg. Weekday Ridership (Oct 2012)</td><td>{{numRiderStr}}</td></tr>
</table>

<h3>Escalator Summary</h3>
<table class="station_escalator_summary">
<tr><td># Escalators</td><td>{{stationSnapshot['numEscalators']}}</td></tr>
<tr><td># Working Escalators</td><td>{{stationSnapshot['numWorking']}}</td></tr>
<tr><td>Current Availability</td><td>{{'%.2f%%'%(100.0*stationSnapshot['availability'])}}</td></tr>
<tr><td>Avg. Availability</td><td>{{'%.2f%%'%(100.0*stationSummary['availability'])}}</td></tr>
</table>


<h3>Escalators</h3>
%hasStationDesc = any(e['stationDesc'] for e in escalators)
<table class="status">
<tr>
    <th>Unit</th>
    %if hasStationDesc:
    <th>Entrance</th>
    %end
    <th>Description</th>
    <th>Current Status</th>
    <th>Avg. Availabilty</th>
</tr>
%for esc in escalators:
%   escWebPath = escUnitIdToWebPath(esc['unitId'])
<tr class={{esc['curSymptomCategory'].lower()}}>
    <td><a href="{{escWebPath}}">{{esc['unitId']}}</a></td>
    %if hasStationDesc:
    <td>{{esc['stationDesc']}}</td>
    %end
    <td>{{esc['escDesc']}}</td>
    <td>{{esc['curStatus']}}</td>
    <td>{{'%.2f%%'%(100.0*esc['availability'])}}</td>
</tr>
%end
</table>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

%rebase layout title=stationSnapshot['name'], description=''
