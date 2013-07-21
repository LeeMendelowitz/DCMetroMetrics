%# Listing of all stations
%from operator import itemgetter
%from metroEscalatorsWeb import lineToColoredSquares
%import hotCarsWeb
%from hotCarsWeb import tweetLinks, formatTimeStr, recToLinkHtml, makeHotCarLink
%from operator import itemgetter
%from metroTimes import toLocalTime

%description="Compilation of crowdsourced reports of #wmata #hotcar's in the WMATA Metrorail system"

<div class="container">
<div class="main-content">

<a id="top"></a>
<h2>HotCars</h2>

<p>Report a hot car on Twitter by tweeting a single 4-digit car number, the line color, and the hashtags #wmata #hotcar.
</p>

<a href="#summary">Summary</a>&nbsp;
<a href="#leaders">Most reported</a>&nbsp;
<a href="#plots">Data Visualizations</a>&nbsp;
<a href="#allreports">All reports</a>&nbsp;

<a id="summary"></a>
<h3>Summary</h3>
<table class="table table-hover table-bordered" style="width:25%; min-width:250px;">
    <tr> <td>Num. Reports</td> <td>{{summary['numReports']}}</td> </tr>
    <tr> <td>Num. Reporters</td> <td>{{summary['numReporters']}}</td> </tr>
    <tr> <td>Num. Cars Reported</td> <td>{{summary['numCars']}}</td> </tr>
    <tr> <td>Avg. reports per day</td> <td>{{'%.1f'%summary['reportsPerDay']}}</td> </tr>
    <tr> <td>Avg. reports per weekday</td> <td>{{'%.1f'%summary['reportsPerWeekday']}}</td> </tr>
</table>

<h3>Most reported (<a href="#top">top</a>) </h3>

<p>
    This table shows the number of #wmata #hotcar reports for each #hotcar over different time periods. Click on the column headers to sort.
</p>
<div id="MostReportedTableChartDiv" style="width:100%;"></div>

<a id="plots"></a>
<h3>Data Visualizations (<a href="#top">top</a>) </h3>
<p>
<a href="#bySeries">by car series</a>&nbsp;
<a href="#byColor">by line color</a>&nbsp;
<a href="#byDate">by date</a>&nbsp;
</p>

<a id="bySeries"></a>
<h4>Reports By Car Series (<a href="#top">top</a>) </h4>
<div id="hotCarsBySeriesBarChartDiv" style="width:100%;"></div>
<div id="hotCarsBySeriesPieChartDiv" style="width:100%;"></div>

<a id="byColor"></a>
<h4>Reports by Line Color (<a href="#top">top</a>)</h4>
<div id="hotCarsByColorBarChartDiv" style="width:100%;"></div>
<div id="hotCarsByColorPieChartDiv" style="width:100%;"></div>

<a id="byDate"></a>
<h4>Reports by Date (<a href="#top">top</a>) </h4>
<p>
    This plot shows the number of daily #wmata #hotcar reports (orange) and
    the daily high temperature for Washington, DC (red).
</p>
<div id="timeSeriesDiv" style="width:700px; height:300px;"></div>

<a id="allreports"></a>
<h3>All reports <a href="#top">(top)</a></h3>

<a href="#reportsByCar">Reports By Car</a>&nbsp;
<a href="#reportsByUser">Reports By User</a>&nbsp;

<a id="reportsByCar"></a>
<h4>Reports by Car Number <a href="#top">(top)</a></h4>
<div id="hotCarTableChartDiv" style="width:100%;"></div>
<div id="hotCarTableManual">
    <table class="hotcars table table-hover table-bordered">
    <tr>
        <th>Car Number</th>
        <th>Color</th>
        <th>Num. Reports</th>
        <th>Last Report Time</th>
        <th>Last Report</th>
        <th>All Reports</th>
    </tr>
    %sortedKeys = sorted(hotCarData.keys(), key = lambda k: hotCarData[k]['numReports'], reverse=True)
    %for carNum in sortedKeys:
    %   data = hotCarData[carNum]
    %   records = data['reports']
    %   lastReport = data['lastReport']
    %   lastReportLink = recToLinkHtml(lastReport, lastReport['handle'])
    %   lastReportTimeStr = formatTimeStr(data['lastReportTime'])
        <tr>
            <td>{{!makeHotCarLink(carNum)}}</td>
            <td>{{!lineToColoredSquares(data['colors'])}}</td>
            <td>{{len(records)}}</td>
            <td>{{lastReportTimeStr}}</td>
            <td>{{!lastReportLink}}</td>
            <td>{{!tweetLinks(records)}}</td>
        </tr>
    %end
    </table>
</div>

<a id="reportsByUser"></a>
<h4>Reports By User (<a href="#top">top</a>) </h4>
<div id="hotCarsByUserTableChartDiv" style="width:100%;"></div>

%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

</div> <!-- end main-content -->
</div> <!-- end container -->

%def scriptsToInclude():
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src="/js/hotCars.js"></script>
%end

%rebase layout title='DC Metro Metrics: HotCars', description=description, scriptsToInclude=scriptsToInclude
