%# Get rankings for escalators

%description = 'Performance rankings of escalators in the WMATA Metrorail system.'

<a id="top"></a>
<h2>Rankings</h2>

<p>Explore which escalators are the most broken, and which stations have the
best and worst performing escalators. Also explore historical daily counts
of escalator breaks and inspections.</p>

<p>
<a href="#escalatorRankings">Escalator Rankings</a>&nbsp;
<a href="#stationRankings">Station Rankings</a>&nbsp;
<a href="#trends">Trends</a>&nbsp;
</p>

<a id="escalatorRankings"></a>
<h3>Escalator Rankings (<a href="#top">top</a>)</h3>
<a href="/glossary" onclick="javascript:void window.open('/glossary','','width=600,height=600,toolbar=0,menubar=0,location=0,status=0,scrollbars=1,resizable=1,left=0,top=0');return false;">Glossary</a>
<p>Sort columns by clicking on the column header.</p>
<div id='escalatorRankingsTableManual'>
%# Disabling due to incorrect escaping of <a> tags in text fields
%#{{!dtRankings.ToHtml()}}
</div>
<div id='escalatorRankingsTableChartDiv'></div>

<a id="stationRankings"></a>
<h3>Station Rankings (<a href="#top">top</a>)</h3>
<a href="/glossary" onclick="javascript:void window.open('/glossary','','width=600,height=600,toolbar=0,menubar=0,location=0,status=0,scrollbars=1,resizable=1,left=0,top=0');return false;">Glossary</a>
<p>Sort columns by clicking on the column header.</p>
<div id="stationRankingsTableChartDiv"></div>

<a id="trends"></a>
<h3>Trends (<a href="#top">top</a>)</h3>
<p>Number of breaks (red) and inspections (blue) per day.</p>
<div id='trendsPlotDiv' style="width:700px; height:300px;"></div>
<p>Note: "Data outages" refer to times when escalator data was not 
collected due to technical difficulties, resulting in low counts.</p>


%tf = '%m/%d/%y %H:%M'
%updateStr = curTime.strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
%include escalatorRankings_js dtRankings=dtRankings, dtDailyCounts=dtDailyCounts, dtStationRankings=dtStationRankings

%rebase layout title='DC Metro Metrics: Escalator Rankings', description=description
