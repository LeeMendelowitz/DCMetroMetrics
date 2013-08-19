%# Listing of all stations
%from operator import itemgetter

%from dcmetrometrics.web import eles as metroEscalatorsWeb
%from dcmetrometrics.common.metroTimes import toLocalTime

<div class="container">
<div class="main-content">

<h2>Stations</h2>
<div id="stationsTableChartDiv" style="width:100%;"></div>

<div id="stationTableManual">
<table class="station_listing table table-hover table-bordered">
<tr>
    <th>Station Name</th>
    <th>Lines</th>
    <th>Station Code</th>
    <th>Escalators</th>
%#    <th>Available Escalators</th>
    <th>Availability</th>
</tr>
%stationRecs = sorted(stationRecs, key = itemgetter('name'))
%for i,rec in enumerate(stationRecs):
%   rowClass = 'oddRow' if i%2 == 1 else 'evenRow'
%   codeStr = ', '.join(rec['codes'])
%   lineStr = ', '.join(rec['lines'])
%   lineStr = metroEscalatorsWeb.lineToColoredSquares(rec['lines'])
%   stationWebPath = metroEscalatorsWeb.stationCodeToWebPath(rec['codes'][0])
<tr class={{rowClass}}>
    <td><a href="{{!stationWebPath}}">{{!rec['name']}}</a></td>
    <td>{{!lineStr}}</td>
    <td>{{codeStr}}</td>
    <td>{{str(rec['numEscalators'])}}</td>
%#    <td>{{rec['numWorking']}}</td>
    <td>{{'%.1f%%'%(100.0*rec['availability'])}}</td>
</tr>
%end
</table>
</div>

%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

</div> <!-- end main-content -->
</div> <!-- end container -->

%def scriptsToInclude():
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src="/js/stations.js"></script>
%end

%rebase layout title='DC Metro Metrics: Stations', scriptsToInclude=scriptsToInclude
