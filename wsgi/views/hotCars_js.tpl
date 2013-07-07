%#Generate javascript for the symptom table
<script type="text/javascript">
  google.load('visualization', '1', {packages: ['corechart', 'table', 'annotatedtimeline']});
</script>

<script type="text/javascript">

var hotCarsJson = {{!dtHotCars.ToJSon()}};
var hotCarsByUserJson = {{!dtHotCarsByUser.ToJSon()}};
var hotCarsBySeriesJson = {{!dtHotCarsBySeries.ToJSon()}};
var hotCarsByColorJson = {{!dtHotCarsByColor.ToJSon()}};
var hotCarsByColorCustomJson = {{!dtHotCarsByColorCustom.ToJSon()}}; // For setting bar column colors
var hotCarsTimeSeriesJson = {{!dtHotCarsTimeSeries.ToJSon()}};

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

    this.hotCarsDT = new google.visualization.DataTable(hotCarsJson);
    this.hotCarsDT.sort([{column: 2, desc: true}]);

    this.hotCarsByUserDT = new google.visualization.DataTable(hotCarsByUserJson);
    this.hotCarsByUserDT.sort([{column: 1, desc: true}]);

    this.hotCarsByColorDT = new google.visualization.DataTable(hotCarsByColorJson);
    this.hotCarsByColorCustomDT = new google.visualization.DataTable(hotCarsByColorCustomJson);
    this.hotCarsBySeriesDT = new google.visualization.DataTable(hotCarsBySeriesJson);
    this.hotCarsTimeSeriesDT = new google.visualization.DataTable(hotCarsTimeSeriesJson);
    
    var dateFormatStr = "MM'/'dd'/'yyyy hh':'mm aa";
    this.dateTimeFormatter = new google.visualization.DateFormat({pattern: dateFormatStr});
    this.dateTimeFormatter.format(this.hotCarsDT, 3);
    this.dateTimeFormatter.format(this.hotCarsByUserDT, 3); 

    this.drawHotCarsLeadersTable = function() {
        var chart = new google.visualization.Table(document.getElementById('MostReportedTableChartDiv'));

        var options = { page:'enable',
                        allowHtml: true,
                        sortAscending: false,
                        sortColumn: 2,
                        showRowNumber: true};

        // Instantiate and draw our chart, passing in some options.
        chart.draw(self.hotCarsDT, options);
    };

    this.drawHotCarsTable = function() {
        self.hotCarsTableChart = new google.visualization.Table(document.getElementById('hotCarTableChartDiv'));

        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 2,
                        showRowNumber: true};

        // Instantiate and draw our chart, passing in some options.
        self.hotCarsTableChart.draw(self.hotCarsDT, options);
    };

    this.drawHotCarsByUserTable = function() {
        self.hotCarsByUserTableChart = new google.visualization.Table(document.getElementById('hotCarsByUserTableChartDiv'));

        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 1,
                        showRowNumber: true};

        // Instantiate and draw our chart, passing in some options.
        self.hotCarsByUserTableChart.draw(self.hotCarsByUserDT, options);
    };


    this.drawColorBarChart = function() {
        var chart = new google.visualization.ColumnChart(document.getElementById('hotCarsByColorBarChartDiv'));

        var options = { isStacked: true,
                        backgroundColor: 'transparent',
                        legend: {position: 'none'},
                        colors: ['blue', 'green', 'orange', 'red', 'yellow', 'gray'],
                        };


        chart.draw(self.hotCarsByColorCustomDT, options);
    };

    this.drawColorPieChart = function() {
        var chart = new google.visualization.PieChart(document.getElementById('hotCarsByColorPieChartDiv'));

        var options = { backgroundColor: 'transparent',
                        colors: ['blue', 'green', 'orange', 'red', 'yellow', 'gray'],
                        height: 300,
                        };


        chart.draw(self.hotCarsByColorDT, options);
    };

    this.drawSeriesBarChart = function() {
        var chart = new google.visualization.ColumnChart(document.getElementById('hotCarsBySeriesBarChartDiv'));

        var options = { backgroundColor: 'transparent',
                        legend: {position: 'none'},
                        };


        chart.draw(self.hotCarsBySeriesDT, options);
    };

    this.drawSeriesPieChart = function() {
        var chart = new google.visualization.PieChart(document.getElementById('hotCarsBySeriesPieChartDiv'));

        var options = { backgroundColor: 'transparent',
                        height: 300
                        };


        chart.draw(self.hotCarsBySeriesDT, options);
    };

    this.drawTimeSeries = function() {
        var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('timeSeriesDiv'));
        var opts = {fill:40,
                    dateFormat: "EEE, MMM d, yyyy",
                    colors: ['orange', 'orange'],
                    thickness: 2};
        chart.draw(self.hotCarsTimeSeriesDT, opts);
    };

    this.drawAll = function()
    {
        // Clear the manual html table
        document.getElementById('hotCarTableManual').innerHTML = "";
        self.drawHotCarsLeadersTable();
        self.drawHotCarsTable();
        self.drawHotCarsByUserTable();
        self.drawColorBarChart();
        self.drawColorPieChart();
        self.drawSeriesBarChart();
        self.drawSeriesPieChart();
        self.drawTimeSeries();
    };
    return true;
};

var plotHandler = new PlotHandler();

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(plotHandler.drawAll);

</script>
