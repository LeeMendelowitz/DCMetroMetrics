%# Page for escalator outages

%from dcmetrometrics.web import eles as metroEscalatorsWeb
%from dcmetrometrics.web.eles import lineToColoredSquares, escUnitIdToWebPath, stationCodeToWebPath
%from dcmetrometrics.common.metroTimes import toLocalTime

<div class="container">
<div class="main-content">

<h2>Escalator Outages</h2>

<h3>Summary</h3>
<table class="table table-hover table-bordered" style="width:25%; min-width:250px;">
<tr><td>Availability</td><td>{{'%.2f%%'%(100.0*systemAvailability['availability'])}} </td></tr>
<tr><td>Weighted Availability</td><td>{{'%.2f%%'%(100.0*systemAvailability['weightedAvailability'])}} </td></tr>
</table>

<h3>Symptom Counts</h3>

<div id='symptomTableManual'>
<table class="symptoms table table-hover" style="width:25%; min-width:250px;">
%totalCount = sum(symptomCounts.itervalues())
%for i,(symptom,count) in enumerate(symptomCounts.most_common()):
 <tr><td>{{symptom}}</td><td>{{'%i'%(count)}}</td></tr>
%end
<tr><td><b>TOTAL</b></td><td><b>{{'%i'%totalCount}}</b></td></tr>
</table>
</div>

<div id="tableChartDiv" style="width=95%; min-width=400px;"></div>
<div id="pieChartDiv" style="width=95%; min-width=400px;"></div>


<h3>Outages</h3>

<div id="outageTableDiv" class="googletable" style="width:100%;"></div>

%hasEntranceData = any(esc['stationDesc'] for esc in escList)
<div id="outageTableManual">
<table class="status table table-hover" style="width:25%; min-width:250px;">
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
<tr class={{esc['symptomCategory'].lower()}}>
    <td>{{!esc['unitIdHtml']}}</a></td>
    <td>{{!esc['stationNameHtml']}}</a></td>
    % if hasEntranceData:
    <td>{{esc['stationDesc']}}</td>
    % end
    <td>{{esc['symptom']}}</td>
    %#<td>{{'%.2f%%'%(100.0*esc['availability'])}}</td>
</tr>
%end
</table>
</div>

%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

</div>
</div>

%def scriptsToInclude():
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src="/js/escalatorOutages.js"></script>
%end

%rebase layout title='DC Metro Metrics: Nonoperational Escalators', scriptsToInclude=scriptsToInclude
