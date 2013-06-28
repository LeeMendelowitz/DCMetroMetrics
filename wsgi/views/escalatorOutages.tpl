%# Page for a station
%import metroEscalatorsWeb
%from metroEscalatorsWeb import lineToColoredSquares, escUnitIdToWebPath, stationCodeToWebPath

<script type="text/javascript" src="https://www.google.com/jsapi"></script>

<h2>Escalator Outages</h2>

<h3>Summary</h3>
<table>
<tr><td>Availability</td><td>{{'%.2f%%'%(100.0*systemAvailability['availability'])}} </td></tr>
<tr><td>Weighted Availability</td><td>{{'%.2f%%'%(100.0*systemAvailability['weightedAvailability'])}} </td></tr>
</table>
<h3>Symptom Counts</h3>

<div id='symptomTable'>
<table class="symptoms">
%totalCount = sum(symptomCounts.itervalues())
%for i,(symptom,count) in enumerate(symptomCounts.most_common()):
 <tr><td>{{symptom}}</td><td>{{'%i'%(count)}}</td></tr>
%end
<tr><td><b>TOTAL</b></td><td><b>{{'%i'%totalCount}}</b></td></tr>
</table>
</div>

<div id="tableChartDiv"></div>
<div id="pieChartDiv"></div>


<h3>Outages</h3>
%hasEntranceData = any(esc['stationDesc'] for esc in escList)
<table class="status">
<tr>
    %if hasEntranceData:
    <th style="width:10%">Unit</th>
    <th style="width:30%">Station</th>
    <th style="width:30%">Entrance</th>
    <th style="width:30%">Status</th>
    %else:
    <th style="width:20%">Unit</th>
    <th style="width:50%">Station</th>
    <th style="width:30%">Status</th>
    %end
</tr>
%for esc in escList:
%   escWebPath = escUnitIdToWebPath(esc['unitId'])
%   stationWebPath = stationCodeToWebPath(esc['stationCode'])
<tr class={{esc['symptomCategory'].lower()}}>
    <td><a href="{{escWebPath}}">{{esc['unitId']}}</a></td>
    <td><a href="{{stationWebPath}}">{{esc['stationName']}}</a></td>
    % if hasEntranceData:
    <td>{{esc['stationDesc']}}</td>
    % end
    <td>{{esc['symptom']}}</td>
    %#<td>{{'%.2f%%'%(100.0*esc['availability'])}}</td>
</tr>
%end
</table>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

%include symptom_chart dt=dtSymptoms

%rebase layout title='DC Metro Metrics: Nonoperational Escalators'
