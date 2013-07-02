%#Generate javascript for the symptom table
<script type="text/javascript">
  google.load('visualization', '1', {packages: ['corechart', 'table']});
</script>

<script type="text/javascript">

var escalatorRankingsJson = {{!dtRankings.ToJSon()}};

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
    var formatter = new google.visualization.NumberFormat({suffix: '%'});
    formatter.format(this.rankingsDT, 4);
    formatter.format(this.rankingsDT, 5);

    this.rankingsTableChart = new google.visualization.Table(document.getElementById('escalatorRankingsTableChartDiv'));

    this.drawRankingsTable = function() {

        var options = { allowHtml: true,
                        sortAscending: true,
                        sortColumn: 1,
                        showRowNumber: true,
                        page: 'enable',
                        pageSize: 25}

        // Instantiate and draw our chart, passing in some options.
        self.rankingsTableChart.draw(self.rankingsDT, options);
    };


    this.drawAll = function()
    {
        self.drawRankingsTable()
    };
    return true;
};

var plotHandler = new PlotHandler();

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(plotHandler.drawAll);

</script>
