%# Listing of all stations
%from operator import itemgetter
%from metroEscalatorsWeb import lineToColoredSquares
%import hotCarsWeb
%from hotCarsWeb import tweetLinks, formatTimeStr, recToLinkHtml
%from operator import itemgetter

<h2>Hot Cars</h2>

<p>Report a hot car on Twitter by tweeting a single 4-digit car number, the line color, and the hashtags #wmata #hotcar.
</p>

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
        <td>{{'%i'%int(carNum)}}</td>
        <td>{{!lineToColoredSquares(data['colors'])}}</td>
        <td>{{len(records)}}</td>
        <td>{{lastReportTimeStr}}</td>
        <td>{{!lastReportLink}}</td>
        <td>{{!tweetLinks(records)}}</td>
    </tr>
%end
</table>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

%rebase layout title='DC Metro Metrics: HotCars'
