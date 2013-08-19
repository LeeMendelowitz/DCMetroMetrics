%# Hot Car Page
%from dcmetrometrics.web.hotcars import formatTimeStr
%from dcmetrometrics.web.eles import lineToColoredSquares
%from dcmetrometrics.common.metroTimes import toLocalTime

%description = "Reports for #wmata #hotcar {0} of the WMATA Metrorail System.".format(carNum)

<div class="container">
<div class="main-content">

<h2>HotCar {{carNum}}</h2>

<h3>Summary</h3>

%lineStr = lineToColoredSquares(colors)
<table class="table table-hover table-striped table-bordered" style="min-width:250px; width:40%">
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

%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

</div>
</div>

%rebase layout title='Hot Car %i'%carNum, description=description
