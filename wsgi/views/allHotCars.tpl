%# List of all hot cars
% import hotCarsWeb
<html>

<head>
    <title>Metro Hot Cars</title>
</head>

<!-- BEGIN BODY -->
<body>
<div id="main">
    <div class="hotcars">
    <table border="1">
    <tr>
        <td>Car Number</td>
        <td>Color</td>
        <td>Num. Reports</td>
        <td>Tweet Links </td>
    </tr>
    %sortedKeys = sorted(hotCarDict.keys(), key = lambda k: len(hotCarDict[k]), reverse=True)
    %for carNum in sortedKeys:
    %   records = hotCarDict[carNum]
        <tr>
            <td>{{carNum}}</td>
            <td>{{!hotCarsWeb.makeColorString(records)}}</td>
            <td>{{len(records)}}</td>
            %# Disable html character escaping\\
            <td>{{!hotCarsWeb.tweetLinks(records)}}</td>
        </tr>
    %end
    </table>
    </div>
</div>
</body>
<!-- END BODY -->

</html>

