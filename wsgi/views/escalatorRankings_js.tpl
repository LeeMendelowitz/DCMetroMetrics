%#Generate javascript for the symptom table
<script type="text/javascript">
  google.load('visualization', '1', {packages: ['corechart', 'table', 'annotatedtimeline']});
</script>

<script type="text/javascript">

var escalatorRankingsJson = {{!dtRankings.ToJSon()}};
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

    this.rankingsDT = new google.visualization.DataTable(escalatorRankingsJson);
    this.rankingsDT.sort([{column: 1, desc: false}]);
    this.stationRankingsDT = new google.visualization.DataTable(stationRankingsJson);

    var formatter = new google.visualization.NumberFormat({suffix: '%'});
    formatter.format(this.rankingsDT, 4);
    formatter.format(this.rankingsDT, 5);
    formatter.format(this.stationRankingsDT, 4);
    formatter.format(this.stationRankingsDT, 5);

    this.dailyCountsDT = new google.visualization.DataTable(dailyCountsJson);

    this.rankingsTableChart = new google.visualization.Table(document.getElementById('escalatorRankingsTableChartDiv'));
    this.dailyTrendsChart = new google.visualization.AnnotatedTimeLine(document.getElementById('trendsPlotDiv'));

    this.drawRankingsTable = function() {

        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 2,
                        showRowNumber: true,
                        page: 'enable',
                        pageSize: 15}

        // Instantiate and draw our chart, passing in some options.
        self.rankingsTableChart.draw(self.rankingsDT, options);
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
    }

    this.drawAll = function()
    {
        document.getElementById('escalatorRankingsTableManual').innerHTML = "";
        self.drawRankingsTable();
        self.drawDailyTrends();
        self.drawStationRankings();
    };

    return true;
};

var plotHandler = new PlotHandler();

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(plotHandler.drawAll);

</script>
