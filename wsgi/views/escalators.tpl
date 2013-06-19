%# Page for a station
%import metroEscalatorsWeb
%from metroEscalatorsWeb import lineToColoredSquares, escUnitIdToWebPath
<html>

<head>
    <link rel="stylesheet" type="text/css" href="/static/statusListing.css">
    <title>All Escalators</title>
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

    <h2>Escalators</h3>

    <table class="status">
    <tr>
        <th>Unit</th>
        <th>Station</th>
        <th>Entrance</th>
        <th>Description</th>
        <th>Status</th>
    </tr>
    %for esc in escalators:
    %   escWebPath = escUnitIdToWebPath(esc['unitId'])
    <tr class={{esc['symptomCategory'].lower()}}>
        <td><a href="{{escWebPath}}">{{esc['unitId']}}</a></td>
        <td>{{esc['stationName']}}</td>
        <td>{{esc['stationDesc']}}</td>
        <td>{{esc['escDesc']}}</td>
        <td>{{esc['symptom']}}</td>
        %#<td>{{'%.2f%%'%(100.0*esc['availability'])}}</td>
    </tr>
    %end
    </table>
</div>

</div> <!-- END container -->
</body>

</html>

