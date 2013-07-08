
<html>
<head>
    <title>DC Metro Metrics: Glossary</title>
    <style>
    body {font-family:Sans-serif;}
    .term {text-decoration:underline; font-weight:bold; display:inline;}
    </style>
</head>

<body>

<a id="top"></a>

<p>
<a href="#outage">Outage</a>&nbsp;<br>
<a href="#break">Break</a>&nbsp;<br>
<a href="#inspection">Inspection</a>&nbsp;<br>
<a href="#availability_esc">Availability (escalator)</a>&nbsp;<br>
<a href="#availability_station">Availability (station)</a>&nbsp;<br>
<a href="#broken_time_percentage">Broken Time Percentage</a><br>
</p>

<div class="definition">
<a id="outage"></a>
<div class="term">Outage:</div> (<a href="#top">top</a>)
<div class="definition_text">
<p>
A period of time for which a specific escalator is not operating
as a moving staircase. This includes instances when the escalator
has been intentionally turned off
for inspection or to serve as a two-way staircase.
</p>
<p>
Note that a single outage can include
transitions between multiple statuses. For example:
"CALLBACK/REPAIR" -&gt; "MINOR REPAIR" -&gt; "MAJOR REPAIR" counts as
a single outage.
</p>
</div>
</div>

<div class="definition">
<a id="break"></a>
<div class="term">Break:</div> (<a href="#top">top</a>)
<div class="definition_text">
<p>
An escalator outage which includes at least one status from this list of broken statuses:
<ul>
<li>CALLBACK/REPAIR</li>
<li>FIRE ALARM/DELUGE SYSTEMS</li>
<li>HANDRAIL</li>
<li>INCIDENT/ACCIDENT</li>
<li>MAJOR REPAIR</li>
<li>MINOR REPAIR</li>
<li>POWER SURGE/OUTAGE</li>
<li>WATER LEAK/INTRUSION</li>
<li>WEATHER RELATED</li>
</ul>
</p>

<p>
If the outage includes multiple broken statuses, it still counts as a single break. For example:
"CALLBACK/REPAIR" -&gt; "MINOR REPAIR" -&gt; "MAJOR REPAIR" counts as single break.
</p>
</div>
</div>

<div class="definition">
<a id="inspection"></a>
<div class="term">Inspection:</div> (<a href="#top">top</a>)
<div class="definition_text">
<p>
An escalator outage which includes a SAFETY INSPECTION or PREV. MAINT. INSPECTION status.
</p>
</div>
</p>
</div>

<div class="definition">
<a id="availability_esc"></a>
<div class="term">Availability (for an escalator):</div> (<a href="#top">top</a>)
<div class="definition_text">
<p>
The percentage of time that Metrorail is open for which the specified escalator is operating
as a moving staircase.
</p>
</div>
</div>

<div class="definition">
<a id="availability_station"></a>
<div class="term">Availability (for a station):</div> (<a href="#top">top</a>)
<div class="definition_text">
<p>
The percentage of escalators at a station which are currently operating as moving staircases.
</p>
<p>
The average availability for a station is the historical average availability for the station
over all times that Metrorail is open.
</p>
</div>
</div>

<div class="definition">
<a id="broken_time_percentage"></a>
<div class="term">Broken Time Percentage:</div> (<a href="#top">top</a>)
<div class="definition_text">
<p>
The percentage of time that Metrorail is open for which the specified escalator has
a status among this list of broken statuses:
<ul>
<li>CALLBACK/REPAIR</li>
<li>FIRE ALARM/DELUGE SYSTEMS</li>
<li>HANDRAIL</li>
<li>INCIDENT/ACCIDENT</li>
<li>MAJOR REPAIR</li>
<li>MINOR REPAIR</li>
<li>POWER SURGE/OUTAGE</li>
<li>WATER LEAK/INTRUSION</li>
<li>WEATHER RELATED</li>
</ul>
</p>
</div>
</div>

</body>
</html>
