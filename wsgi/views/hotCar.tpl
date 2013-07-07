%# Hot Car Page
%from hotCarsWeb import formatTimeStr
%from metroEscalatorsWeb import lineToColoredSquares

<h2>HotCar {{carNum}}</h2>

<h3>Summary</h3>

%lineStr = lineToColoredSquares(colors)
<table>
<tr><td>Num. Reports</td><td>{{numReports}}</td></tr>
<tr><td>Lines</td><td>{{!lineStr}}</td></tr>
<tr><td>Last Report Time</td><td>{{lastReportTimeStr}}</td></tr>
</table>

<h3>Reports</h3>

<div class="tweettimeline">
%for report in reports:
<div class="tweetcontainer">
{{!formatTimeStr(report['time'])}}
{{!report['embed_html']}}
</div>
<br style="clear:both;">
%end
</div>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

%rebase layout title='Hot Car %i'%carNum
