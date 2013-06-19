%# Listing of all stations
%from operator import itemgetter
%from metroEscalatorsWeb import lineToColoredSquares
%import hotCarsWeb

<html>

<head>
    <link rel="stylesheet" type="text/css" href="/static/statusListing.css">
    <title>Hot Cars</title>
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

    <h2>Hot Cars</h2>

    <p>Report a hot car on Twitter by tweeting a single 4-digit car number, the line color, and the hashtags #wmata #hotcar.
    </p>

    <table class="hotcars">
    <tr>
        <th>Car Number</th>
        <th>Color</th>
        <th>Num. Reports</th>
        <th>Tweet Links </th>
    </tr>
    %sortedKeys = sorted(hotCarDict.keys(), key = lambda k: len(hotCarDict[k]), reverse=True)
    %for carNum in sortedKeys:
    %   records = hotCarDict[carNum]
    %   colors = [rec['color'] for rec in records]
    %   colors = list(set(c for c in colors if c != 'NONE'))
        <tr>
            <td>{{'%i'%int(carNum)}}</td>
            <td>{{!lineToColoredSquares(colors)}}</td>
            <td>{{len(records)}}</td>
            %# Disable html character escaping\\
            <td>{{!hotCarsWeb.tweetLinks(records)}}</td>
        </tr>
    %end
    </table>

</div>

</div> <!-- END container -->
</body>

</html>

