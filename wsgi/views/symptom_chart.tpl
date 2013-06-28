%#Generate javascript for the symptom table
<script type="text/javascript">
  google.load('visualization', '1', {packages: ['corechart', 'table']});
</script>

<script type="text/javascript">

var data_json = {{!dt.ToJSon()}};

var PlotHandler = function()
{
    var self = this;
    this.dataTable = new google.visualization.DataTable(data_json);
    this.dataTable.sort([{column: 1, desc: true}]);

    // Compute the total symptom count
    var keys = [{column:0, modifier:function(val){ return 1;}, type:'number'}]; // Group all rows together
    var columns = [{column : 1, 'aggregation' : google.visualization.data.sum, 'type' : 'number'}];
    this.totalCount = google.visualization.data.group(this.dataTable, keys, columns).getValue(0,1);

    this.pieChart = new google.visualization.PieChart(document.getElementById('pieChartDiv'));
    this.tableChart = new google.visualization.Table(document.getElementById('tableChartDiv'));
//    this.tableChartAsc = new google.visualization.Table(document.getElementById('tableChartDivAsc'));
 //   this.tableChartDesc = new google.visualization.Table(document.getElementById('tableChartDivDesc'));

    this.drawPieChart = function() {

        // Set chart options
        var options = { width:600,
                       height:400,
                       backgroundColor: {fill: 'transparent', stroke: 'black', strokeWidth: 0},
                       chartArea : {width:'100%'}
                       };

        // Instantiate and draw our chart, passing in some options.
        self.pieChart.draw(self.dataTable, options);
    };

    // Define a sort handler to keep the Total row in the
    // last row.
    this.tableSortHandler = function(e)
    {
        var msg = '\nGot event: Ascending: ' + e.ascending + ', col: ' + e.column;
        //alert(msg);

        var dtClone = self.dataTable.clone();

        // Apply the sort to the cloned table
        dtClone.sort({column : e.column, desc: !e.ascending});

        // Add a row with the Total Symptom Count
        dtClone.addRow(['TOTAL', self.totalCount]);
        var lastRow = dtClone.getNumberOfRows()-1;
        var lastRowPropertyLeft = {style : 'font-weight:bold; border-top:1px solid black; text-align:left;'};
        var lastRowPropertyRight = {style : 'font-weight:bold; border-top:1px solid black; text-align:right;'};
        dtClone.setProperties(lastRow,0, lastRowPropertyLeft);
        dtClone.setProperties(lastRow,1, lastRowPropertyRight);


        var config = {sort : 'event', sortAscending : e.ascending, sortColumn : e.column, width:600, allowHtml: true};
        self.tableChart.draw(dtClone, config);
    };
    this.tableReadyHandler = function()
    {
        var sortInfo = self.tableChart.getSortInfo();
        var msg = 'Table is ready!\nCur Sort info: acending=' + sortInfo['ascending'] + ', col=' + sortInfo['column'] + '.';
        //alert(msg);
    };

    this.drawTableChart = function() {
        var dtClone = self.dataTable.clone();
        dtClone.sort([{column: 1, desc: true}]);
        dtClone.addRow(['TOTAL', self.totalCount])

        var config = {sort: 'event', sortAscending: false, sortColumn : 1, width : 600, allowHtml: true};
        var lastRow = dtClone.getNumberOfRows()-1;
        var lastRowPropertyLeft = {style : 'font-weight:bold; border-top:1px solid black; text-align:left;'};
        var lastRowPropertyRight = {style : 'font-weight:bold; border-top:1px solid black; text-align:right;'};
        dtClone.setProperties(lastRow,0, lastRowPropertyLeft);
        dtClone.setProperties(lastRow,1, lastRowPropertyRight);
        self.tableChart.draw(dtClone, config);

    };
    
    // Add table listeners
    google.visualization.events.addListener(this.tableChart, 'sort', this.tableSortHandler);
    google.visualization.events.addListener(this.tableChart, 'ready',  this.tableReadyHandler);

    this.drawAll = function()
    {
        // Clear the manual html table
        document.getElementById('symptomTable').innerHTML = "";
        self.drawPieChart();
        self.drawTableChart();
    };
    return true;
};

var plotHandler = new PlotHandler();

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(plotHandler.drawAll);

</script>
