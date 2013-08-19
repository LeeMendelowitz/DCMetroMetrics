%#Generate javascript for the symptom table
%from dcmetrometrics.web.eles import pyDictToJS

google.load('visualization', '1', {packages: ['corechart', 'table', 'annotatedtimeline']});

%#Unpack the rankingsDict

%numRankings = len(rankingsDict)
var rankingsJSON = {
%for i,(k,data) in enumerate(rankingsDict.iteritems()):
{{k}} : {{!data['dataTable'].ToJSon()}} {{',' if i < numRankings-1 else ''}}
%end
};

var rankingsHeaders = {
%for i,(k,data) in enumerate(rankingsDict.iteritems()):
{{k}} : "{{data['header']}}" {{',' if i < numRankings-1 else ''}}
%end
};

%#var rankingsData = {{!pyDictToJS(rankingsDict)}};
var dailyCountsJson = {{!dtDailyCounts.ToJSon()}};
var stationRankingsJson = {{!dtStationRankings.ToJSon()}};

// Set the property for an entire datatable row, cell by cell
var setRowProperty = function(dt, rowNum, property)
{
    var numCols = dt.getNumberOfColumns();
    for(var i=0; i<numCols; i++)
    {
        dt.setProperties(rowNum, i, property);
    }
    return true;
};

var PlotHandler = function()
{
    var self = this;

    var formatter = new google.visualization.NumberFormat({suffix: '%'});
    this.allRankingsDt = {
    %numK = len(rankingsDict)
    %for i,(k,dt) in enumerate(rankingsDict.iteritems()):
    {{k}} : new google.visualization.DataTable(rankingsJSON.{{k}}) {{',' if i < numK-1 else ''}}
    %end
    };

    this.stationRankingsDT = new google.visualization.DataTable(stationRankingsJson);

    //Format percentages in DataTables
    for (x in this.allRankingsDt)
    {
        formatter.format(this.allRankingsDt[x], 4);
        formatter.format(this.allRankingsDt[x], 5);
    }
    formatter.format(this.stationRankingsDT, 4);
    formatter.format(this.stationRankingsDT, 5);

    this.dailyCountsDT = new google.visualization.DataTable(dailyCountsJson);

    this.rankingsTableChart = new google.visualization.Table(document.getElementById('escalatorRankingsTableChartDiv'));
    this.dailyTrendsChart = new google.visualization.AnnotatedTimeLine(document.getElementById('trendsPlotDiv'));

    //Key should be '1d', '3d', '7d', '14d', '28d', or 'AllTime'
    this.drawRankingsTable = function(key) {

        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 2,
                        showRowNumber: true,
                        page: 'enable',
                        pageSize: 15}

        // Instantiate and draw our chart, passing in some options.
        self.rankingsTableChart.draw(self.allRankingsDt[key], options);

        // Change the header
        document.getElementById('escRankings_header').innerHTML = rankingsHeaders[key] + " Rankings";
    };

    this.drawDailyTrends = function() {
        var options = { displayAnnotations : true,
                        fill: 30,
                        colors: ['red', 'blue'],
                        dateFormat: "EEE, MMM d, yyyy",
                        thickness: 2};
        self.dailyTrendsChart.draw(self.dailyCountsDT, options);
    };

    this.drawStationRankings = function() {
        var chart = new google.visualization.Table(document.getElementById('stationRankingsTableChartDiv'));
        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 5,
                        showRowNumber: true,
                        page: 'enable',
                        pageSize: 15}
        chart.draw(self.stationRankingsDT, options);
    };

    this.setEscalatorRankingLinks = function()
    {
        for (var k in rankingsHeaders)
        {
            var a = document.getElementById("escRankings_" + k);

            var makeOnClickFunc = function()
            {
                var myKey = k;
                var clickFunc = function(){
                    self.drawRankingsTable(myKey);
                    return false;
                }
                return clickFunc;
            };

            a.onclick = makeOnClickFunc();
        }
    };

    this.drawAll = function()
    {
        self.setEscalatorRankingLinks();
        document.getElementById('escalatorRankingsTableManual').innerHTML = "";
        document.getElementById('sort_instructions').innerHTML = "Sort columns by clicking on the column header.";
        self.drawRankingsTable("AllTime");
        self.drawDailyTrends();
        self.drawStationRankings();
    };

    return true;
};

var drawPlots = function(){
    var plotHandler = new PlotHandler();
    plotHandler.drawAll();
};

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(drawPlots);
