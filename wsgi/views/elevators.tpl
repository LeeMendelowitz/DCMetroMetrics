%# Page for a station
%import metroEscalatorsWeb
%from metroEscalatorsWeb import lineToColoredSquares, eleUnitIdToWebPath, stationCodeToWebPath, symptomCategoryToClass
%from metroTimes import toLocalTime

<div class="container">
<div class="main-content">

<h2>Elevators</h2>

%stationNames = sorted(stationToEsc.keys())
%stationLetters = set(sn[0].upper() for sn in stationNames)
%seenLetters = set()

%#Create a list of bookmark links by letter
% for letter in sorted(stationLetters):
<a href="#{{letter}}">{{letter}}</a>
% end

%for station in stationNames:
%   escList = stationToEsc[station]
%   if not escList:
%      continue
%   end
%   stationCode = escList[0]['stationCode']
%   stationWebPath = stationCodeToWebPath(stationCode)
%   hasEntranceData = any(esc['stationDesc'] for esc in escList)
%   firstLetter = station[0].upper()
%   sawFirstLetter = firstLetter in seenLetters
%   if not sawFirstLetter:
%      seenLetters.add(firstLetter)
%   end
<div>
% if sawFirstLetter:
<a href={{stationWebPath}}><h3>{{station}}</h3></a>
% else:
% #Seeing this letter for first time, add a bookmark
<a id="{{firstLetter}}">
<a href={{stationWebPath}}><h3>{{station}}</h3></a>
</a>
% end

<table class="status table tabe-border table-hover table-striped">
<tr>
    <th>Unit</th>
    % if hasEntranceData:
    <th>Entrance</th>
    % end
    <th>Description</th>
    <th>Status</th>
</tr>
%   for esc in escList:
%      escWebPath = eleUnitIdToWebPath(esc['unitId'])
%      symptomCat = esc['symptomCategory'].lower()
<tr class={{symptomCategoryToClass[symptomCat]}}>
    <td><a href="{{escWebPath}}">{{esc['unitId']}}</a></td>
    % if hasEntranceData:
    <td>{{esc['stationDesc']}}</td>
    % end
    <td>{{esc['escDesc']}}</td>
    <td>{{esc['symptom']}}</td>
    %#<td>{{'%.2f%%'%(100.0*esc['availability'])}}</td>
</tr>
%   end
</table>
</div>
%end

%tf = '%m/%d/%y %I:%M %p'
%updateStr = toLocalTime(curTime).strftime(tf)
<div class=updateTime>
<p>Page Last Updated: {{updateStr}}</p>
</div>

</div>
</div>

%rebase layout title='DC Metro Metrics: All Elevators', description=''
