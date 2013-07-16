%# Get rankings for escalators
%from metroTimes import toLocalTime

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

<!-- ESCALATOR RANKINGS -->
<a id="escalatorRankings"></a>
<h3>Escalator Rankings (<a href="#top">top</a>)</h3>
<p id="sort_instructions"></p>
<p><a href="/glossary" onclick="javascript:void window.open('/glossary','','width=600,height=600,toolbar=0,menubar=0,location=0,status=0,scrollbars=1,resizable=1,left=0,top=0');return false;">Glossary</a></p>

<!-- Rankings table for those without Javascript -->
<div id='escalatorRankingsTableManual'>
%# Disabling due to incorrect escaping of <a> tags in text fields
%#{{!dtRankings.ToHtml()}}
</div>

<!-- Rankings table for those with Javascript -->
<div style="font: 8px;">
<a id="escRankings_d1" href="#">1d</a>&nbsp;
<a id="escRankings_d3" href="#">3d</a>&nbsp;
<a id="escRankings_d7" href="#">7d</a>&nbsp;
<a id="escRankings_d14" href="#">14d</a>&nbsp;
<a id="escRankings_d28" href="#">28d</a>&nbsp;
<a id="escRankings_AllTime" href="#">All Time</a><br><br>
</div>
<div style="font-weight:bold;" id="escRankings_header"></div>
<div id='escalatorRankingsTableChartDiv'></div>

<!-- STATION RANKINGS -->
<a id="stationRankings"></a>
<h3>Station Rankings (<a href="#top">top</a>)</h3>
<a href="/glossary" onclick="javascript:void window.open('/glossary','','width=600,height=600,toolbar=0,menubar=0,location=0,status=0,scrollbars=1,resizable=1,left=0,top=0');return false;">Glossary</a>
<div id="stationRankingsTableChartDiv"></div>

<a id="trends"></a>
<h3>Trends (<a href="#top">top</a>)</h3>
<p>Number of breaks (red) and inspections (blue) per day.</p>
<div id='trendsPlotDiv' style="width:700px; height:300px;"></div>
<p>Note: "Data outages" refer to times when escalator data was not 
collected due to technical difficulties, resulting in low counts.</p>


%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src="/js/escalatorRankings.js"></script>

%rebase layout title='DC Metro Metrics: Escalator Rankings', description=description
