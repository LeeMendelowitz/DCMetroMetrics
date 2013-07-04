%# Get rankings for escalators


<h2>Escalator Rankings</h2>

<p>Sort columns by clicking on the header.</p>
<div id='escalatorRankingsTableManual'>
%# Disabling due to incorrect escaping of <a> tags in text fields
%#{{!dtRankings.ToHtml()}}
</div>
<div id='escalatorRankingsTableChartDiv'></div>

<h2>Trends</h2>
<div id='trendsPlotDiv' style="width:700px; height:300px;"></div>
<p>Note: "Data outages" refer to times when escalator data was not 
collected due to technical difficulties, resulting in low counts.</p>

%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
%include escalatorRankings_js dtRankings=dtRankings, dtDailyCounts=dtDailyCounts

%rebase layout title='DC Metro Metrics: Escalator Rankings'
