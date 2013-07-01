%#Generate javascript for the symptom table
<script type="text/javascript">
  google.load('visualization', '1', {packages: ['corechart', 'table']});
</script>

<script type="text/javascript">

var hotCarsJson = {{!dtHotCars.ToJSon()}};
var hotCarsByUserJson = {{!dtHotCarsByUser.ToJSon()}};

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
    
    var dateFormatStr = "MM'/'dd'/'yyyy hh':'mm aa";
    this.dateTimeFormatter = new google.visualization.DateFormat({pattern: dateFormatStr});
    this.dateTimeFormatter.format(this.hotCarsDT, 3);
    this.dateTimeFormatter.format(this.hotCarsByUserDT, 3); 
    this.hotCarsTableChart = new google.visualization.Table(document.getElementById('hotCarTableChartDiv'));
    this.hotCarsByUserTableChart = new google.visualization.Table(document.getElementById('hotCarsByUserTableChartDiv'));

    this.drawHotCarsTable = function() {

        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 2};

        // Instantiate and draw our chart, passing in some options.
        self.hotCarsTableChart.draw(self.hotCarsDT, options);
    };

    this.drawHotCarsByUserTable = function() {

        var options = { allowHtml: true,
                        sortAscending: false,
                        sortColumn: 1};

        // Instantiate and draw our chart, passing in some options.
        self.hotCarsByUserTableChart.draw(self.hotCarsByUserDT, options);
    };

    this.drawAll = function()
    {
        // Clear the manual html table
        document.getElementById('hotCarTableManual').innerHTML = "";
        self.drawHotCarsTable();
        self.drawHotCarsByUserTable();
    };
    return true;
};

var plotHandler = new PlotHandler();

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(plotHandler.drawAll);

</script>
