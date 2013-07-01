%# Listing of all stations
%from operator import itemgetter
%import metroEscalatorsWeb


<h2>Stations</h2>
<div id="stationsTableChartDiv"></div>

<div id="stationTableManual">
<table class="station_listing">
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

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
%include stations_js dtStations=dtStations

%rebase layout title='DC Metro Metrics: Stations'
