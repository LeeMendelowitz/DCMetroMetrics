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
    <table>
    %for carNum, records in hotCarDict.iteritems():
        <tr>
            <td>{{carNum}}</td>
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

