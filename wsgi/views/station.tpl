%# Page for a station
%from dcmetrometrics.web import eles as metroEscalatorsWeb
%from dcmetrometrics.web.eles import lineToColoredSquares, escUnitIdToWebPath, eleUnitIdToWebPath, symptomCategoryToClass
%from dcmetrometrics.common.metroTimes import toLocalTime
    
%#station data
%codeStr = ', '.join(stationSnapshot['allCodes'])
%lineStr = lineToColoredSquares(stationSnapshot['allLines'])
%numRiderStr = '{:,d}'.format(stationSnapshot['numRiders'])

<div class="container">
<div class="main-content">

<h2>{{stationSnapshot['name']}}</h2>

<h3>Station Data</h3>
<table class="station_data table table-hover table-bordered table-striped" style="width:40%; min-width:250px;">
<tr> <td>Station Name</td><td>{{stationSnapshot['name']}}</td> </tr>
<tr> <td>Station Codes</td><td>{{codeStr}}</td> </tr>
<tr> <td>Station Lines</td><td>{{!lineStr}} </td></tr>
<tr> <td>Avg. Weekday Ridership (Oct 2012)</td><td>{{numRiderStr}}</td></tr>
</table>

<h3>Escalator Summary</h3>
<table class="station_escalator_summary table table-hover table-bordered table-striped" style="width:25%; min-width:250px;">
<tr><td># Escalators</td><td>{{stationSnapshot['numEscalators']}}</td></tr>
<tr><td># Working Escalators</td><td>{{stationSnapshot['numEscWorking']}}</td></tr>
<tr><td>Current Availability</td><td>{{'%.2f%%'%(100.0*stationSnapshot['escAvailability'])}}</td></tr>
<tr><td>Avg. Availability</td><td>{{'%.2f%%'%(100.0*stationSummary['availability'])}}</td></tr>
</table>


<h3>Escalators</h3>
%hasStationDesc = any(e['stationDesc'] for e in escalators)
<table class="status table table-hover table table-striped">
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
%   symptomCat = esc['curSymptomCategory'].lower()
<tr class={{symptomCategoryToClass[symptomCat]}}>
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

<h3>Elevators</h3>
%hasStationDesc = any(e['stationDesc'] for e in elevators)
<table class="status table table-hover table table-striped">
<tr>
    <th>Unit</th>
    %if hasStationDesc:
    <th>Entrance</th>
    %end
    <th>Description</th>
    <th>Current Status</th>
    <th>Avg. Availabilty</th>
</tr>
%for ele in elevators:
%   eleWebPath = eleUnitIdToWebPath(ele['unitId'])
%   symptomCat = ele['curSymptomCategory'].lower()
<tr class={{symptomCategoryToClass[symptomCat]}}>
    <td><a href="{{eleWebPath}}">{{ele['unitId']}}</a></td>
    %if hasStationDesc:
    <td>{{ele['stationDesc']}}</td>
    %end
    <td>{{ele['escDesc']}}</td>
    <td>{{ele['curStatus']}}</td>
    <td>{{'%.2f%%'%(100.0*ele['availability'])}}</td>
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

%rebase layout title=stationSnapshot['name'], description=''
