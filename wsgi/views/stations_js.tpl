%#Generate javascript for the symptom table
google.load('visualization', '1', {packages: ['corechart', 'table']});

var stationsJson = {{!dtStations.ToJSon()}};

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

    this.stationsDT = new google.visualization.DataTable(stationsJson);
    this.stationsDT.sort([{column: 0, desc: false}]);
    var formatter = new google.visualization.NumberFormat({suffix: '%'});
    formatter.format(this.stationsDT, 4);

    this.stationsTableChart = new google.visualization.Table(document.getElementById('stationsTableChartDiv'));

    this.drawStationsTable = function() {

        var options = { allowHtml: true,
                        sortAscending: true,
                        sortColumn: 0};

        // Instantiate and draw our chart, passing in some options.
        self.stationsTableChart.draw(self.stationsDT, options);
    };


    this.drawAll = function()
    {
        // Clear the manual html table
        document.getElementById('stationTableManual').innerHTML = "";
        self.drawStationsTable();
    };
    return true;
};

var drawPlots = function()
{
    var plotHandler = new PlotHandler();
    plotHandler.drawAll();
    return true;
};

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(drawPlots);
