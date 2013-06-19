%# Listing of all stations
%from operator import itemgetter
%import metroEscalatorsWeb

<html>

<head>
    <link rel="stylesheet" type="text/css" href="/static/statusListing.css">
    <title>Stations</title>
</head>

<!-- BEGIN BODY -->

<body>

<div id="maincontainer">

<div id="header">
%include header
</div>

<div id="leftcolumn">
%include left_column
</div>

<div id="contentwrapper">

    <h2>Stations</h2>

    <table class="station_listing">
    <tr>
        <th>Station Name</th>
        <th>Lines</th>
        <th>Station Code</th>
        <th>Escalators</th>
        <th>Available Escalators</th>
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
        <td>{{rec['numWorking']}}</td>
        <td>{{'%.2f'%(100.0*rec['availability'])}}</td>
    </tr>
    %end
    </table>
</div>

</div> <!-- END container -->
</body>

</html>

