%# Get rankings for escalators


<h2>Escalator Rankings Table</h2>
<div id='escalatorRankingsTableChartDiv'></div>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
%include escalatorRankingsTable_js dtRankings=dtRankings

%rebase layout title='DC Metro Metrics: Escalator Rankings'
