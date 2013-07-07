%# Listing of all stations
%from operator import itemgetter
%from metroEscalatorsWeb import lineToColoredSquares
%import hotCarsWeb
%from hotCarsWeb import tweetLinks, formatTimeStr, recToLinkHtml, makeHotCarLink
%from operator import itemgetter

<a id="top"></a>
<h2>Hot Cars</h2>

<p>Report a hot car on Twitter by tweeting a single 4-digit car number, the line color, and the hashtags #wmata #hotcar.
</p>

<a href="#summary">Summary</a>&nbsp;
<a href="#leaders">Most reported</a>&nbsp;
<a href="#plots">Data Visualizations</a>&nbsp;
<a href="#allreports">All reports</a>&nbsp;

<a id="summary"></a>
<h3>Summary</h3>
<table>
    <tr> <td>Num. Reports</td> <td>{{summary['numReports']}}</td> </tr>
    <tr> <td>Num. Reporters</td> <td>{{summary['numReporters']}}</td> </tr>
    <tr> <td>Num. Cars Reported</td> <td>{{summary['numCars']}}</td> </tr>
    <tr> <td>Avg. reports per day</td> <td>{{'%.1f'%summary['reportsPerDay']}}</td> </tr>
    <tr> <td>Avg. reports per weekday</td> <td>{{'%.1f'%summary['reportsPerWeekday']}}</td> </tr>
</table>

<h3>Most reported (<a href="#top">top</a>) </h3>

<div id="MostReportedTableChartDiv"></div>

<a id="plots"></a>
<h3>Data Visualizations (<a href="#top">top</a>) </h3>
<p>
<a href="#bySeries">by car series</a>&nbsp;
<a href="#byColor">by line color</a>&nbsp;
<a href="#byDate">by date</a>&nbsp;
</p>

<a id="bySeries"></a>
<h4>Reports By Car Series (<a href="#top">top</a>) </h4>
<div id="hotCarsBySeriesBarChartDiv"></div>
<div id="hotCarsBySeriesPieChartDiv"></div>

<a id="byColor"></a>
<h4>Reports by Line Color (<a href="#top">top</a>)</h4>
<div id="hotCarsByColorBarChartDiv"></div>
<div id="hotCarsByColorPieChartDiv"></div>

<a id="byDate"></a>
<h4>Reports by Date (<a href="#top">top</a>) </h4>
<div id="timeSeriesDiv" style="width:700px; height:300px;"></div>

<a id="allreports"></a>
<h3>All reports <a href="#top">(top)</a></h3>

<a href="#reportsByCar">Reports By Car</a>&nbsp;
<a href="#reportsByUser">Reports By User</a>&nbsp;

<a id="reportsByCar"></a>
<h4>Reports by Car Number <a href="#top">(top)</a> </h4>
<div id="hotCarTableChartDiv"></div>
<div id="hotCarTableManual">
    <table class="hotcars">
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
<div id="hotCarsByUserTableChartDiv"></div>


%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
%include hotCars_js dtHotCars=dtHotCars, dtHotCarsByUser=dtHotCarsByUser, dtHotCarsBySeries=dtHotCarsBySeries, dtHotCarsByColor=dtHotCarsByColor, dtHotCarsByColorCustom=dtHotCarsByColorCustom, dtHotCarsTimeSeries=dtHotCarsTimeSeries

%rebase layout title='DC Metro Metrics: HotCars'
