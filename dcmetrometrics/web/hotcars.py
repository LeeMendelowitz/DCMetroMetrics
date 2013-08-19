from operator import itemgetter
from collections import defaultdict, Counter
from datetime import datetime, date, timedelta

from ..third_party import gviz_api
from ..third_party.twitter import TwitterError
from ..common.metroTimes import toLocalTime, utcnow
from .eles import lineToColoredSquares
from ..hotcars import hotCars


def makeTwitterUrl(handle, statusId):
    s = 'https://www.twitter.com/{handle}/status/{statusId:d}'
    return s.format(handle=handle, statusId=statusId)

def recToLinkHtml(rec, text=None):
    handle = rec['handle']
    if text is None:
        text = handle
    tweetId = int(rec['tweet_id'])
    url = makeTwitterUrl(handle, tweetId)
    s = '<a href="{url}" target="_blank">{text}</a>'
    return s.format(url=url, text=text)

def makeHotCarLink(carNum):
    path = '/hotcars/%i'%carNum
    s = '<a href="{path}">{num}</a>'.format(path=path, num=carNum)
    return s

def formatTimeStr(dt):
    tf = '%m/%d/%y %I:%M %p'
    return dt.strftime(tf)

def tweetLinks(records):
    linkHtmls = [recToLinkHtml(rec, str(i+1)) for i, rec in enumerate(records)]
    linkString = ' '.join(linkHtmls)
    return linkString

def twitterHandleLink(handle):
    link = 'http://twitter.com/%s'%handle
    output = '<a href={link} target="_blank">{text}</a>'.format(link=link, text=handle)
    return output

def makeColorString(records):
    colors = [rec['color'] for rec in records]
    colors = [c for c in colors if c != 'NONE']
    colors = set(colors)
    colorStr = ', '.join(colors)
    return colorStr

#####################################################
# Return a dictionary from hot car number to the list
# of reports for that hot car.
# Convert all times to local times.
def getHotCarToReports(db):

    # Car number to reports
    hotCarToReports = hotCars.getAllHotCarReports(db)

    for carNum, reports in hotCarToReports.iteritems():
        for r in reports:
            r['time'] = toLocalTime(r['time'])

    return hotCarToReports

####################################################
# Return a list of hot car reports for a single car.
# Convert all times to local time zone
def getHotCarReportsForCar(db, carNum):
    reports = hotCars.getHotCarReportsForCar(db, carNum)
    for r in reports:
        r['time'] = toLocalTime(r['time'])
    return reports

def getAllHotCarData(db):

    # Car number to reports
    hotCarToReports = getHotCarToReports(db)


    # Summarize this data
    carNumToData = {}
    for carNum, reports in hotCarToReports.iteritems():
        # Sort reports in cronological order
        reports = sorted(reports, key = itemgetter('time'))
        # Get the most recent report time
        mostRecentTime = reports[-1]['time']
        colors = [rec['color'] for rec in reports]
        colors = list(set(c for c in colors if c != 'NONE'))
        # Get the colors of the car
        data = { 'reports' : reports,
                 'numReports' : len(reports),
                 'colors' : colors,
                 'lastReportTime' : mostRecentTime,
                 'lastReport' : reports[-1],
                 'carNum' : carNum}
        carNumToData[carNum] = data

    return carNumToData


def hotCarGoogleTable(hotCarData):

    curTime = toLocalTime(utcnow())

    def countReportsLastNDays(reports, n):
        minTime = curTime - timedelta(days=n)
        return sum(1 for r in reports if r['time'] >= minTime)

    # Make a DataTable with this data
    schema = [('carNum', 'string', 'Car'),
              ('line', 'string', 'Line'),
              ('numReports', 'number', 'Num. Reports'),
              ('1d', 'number','1d'),
              ('3d', 'number','3d'),
              ('7d', 'number','7d'),
              ('14d', 'number', '14d'),
              ('28d', 'number', '28d'),
              ('lastReportTime', 'datetime', 'Last Report Time'),
              #('lastReport', 'string', 'Last Report'),
             # ('allReports', 'string', 'All Reports'),
              ]
    rowData = []

    for d in hotCarData.itervalues():
        lastReport = d['lastReport']
        reports = d['reports']
        row = [makeHotCarLink(d['carNum']),
               lineToColoredSquares(d['colors']),
               len(d['reports']),
               countReportsLastNDays(reports, 1),
               countReportsLastNDays(reports, 3),
               countReportsLastNDays(reports, 7),
               countReportsLastNDays(reports, 14),
               countReportsLastNDays(reports, 28),
               d['lastReportTime'],
               #recToLinkHtml(lastReport, lastReport['handle']),
               #tweetLinks(d['reports'])
               ]
        rowData.append(row)
    dtHotCars = gviz_api.DataTable(schema, rowData)
    return dtHotCars

def getHotCarDataByUser(db):

    # Car number to reports
    hotCarToReports = getHotCarToReports(db)

    reportsByUser = defaultdict(list)
    reports = (d for dlist in hotCarToReports.itervalues() for d in dlist)
    for r in reports:
        reportsByUser[r['handle']].append(r)

    userToReportData = {}
    for handle in reportsByUser.iterkeys():
        reports = reportsByUser[handle]
        reports = sorted(reports, key = itemgetter('time'))
        reportsByUser[handle] = reports
        numReports = len(reports)
        lastReportTime = reports[-1]['time']
        lines = (r['color'] for r in reports)
        lines = list(set(l for l in lines if l != 'NONE'))
        d = {'reports' : reports,
             'lastReportTime' : lastReportTime,
             'lines' : lines,
             'numReports' : numReports,
             'handle' : handle}
        userToReportData[handle] = d

    return userToReportData

def hotCarByUserGoogleTable(db):

    userHotCarData = getHotCarDataByUser(db)
    
    # Make a DataTable with this data
    schema = [('Handle', 'string', 'Handle'),
              ('numReports', 'number', 'Num. Reports'),
              ('lines', 'string', 'Lines'),
              ('lastReport', 'datetime', 'Last Report Time'),
              ('reports', 'string', 'Reports')]

    rowData = []
    for d in userHotCarData.itervalues():
        row = [twitterHandleLink(d['handle']),
               d['numReports'],
               lineToColoredSquares(d['lines']),
               d['lastReportTime'],
               tweetLinks(d['reports'])]
        rowData.append(row)
    dtHotCarsByUser = gviz_api.DataTable(schema, rowData)
    return dtHotCarsByUser

# Get web page data for a single hot car
def getHotCarData(db, carNum):

    # Get all hot car reports for this car num
    reports = getHotCarReportsForCar(db, carNum)

    # Get the tweet embedding html.
    for report in reports:
        tweetId = int(report['tweet_id'])
        tweetData = db.hotcars_tweets.find_one(tweetId)
        report['embed_html'] = tweetData.get('embed_html', '')

    numReports = len(reports)
    colors = [r['color'] for r in reports]
    colors = list(set(c for c in colors if c != 'NONE'))
    reports = sorted(reports, key = itemgetter('time'), reverse=True)
    tweetHtmls = [t['embed_html'] for t in reports]

    ret = { 'numReports' : numReports,
            'colors' : colors,
            'tweetHtmls' : tweetHtmls,
            'reports' : reports}
    return ret

#############################
def makeCarSeriesGoogleTable(seriesToCount):
    series = [str(i) for i in range(1,7)]

    schema = [('Series', 'string', 'Series'),
              ('Count', 'number', 'Count')]
    rowData = [(s+'000', seriesToCount.get(s,0)) for s in series]
    dtSeriesCount = gviz_api.DataTable(schema, rowData)
    return dtSeriesCount

#############################
def makeColorCountsGoogleTable(colorToCount):
    schema = [('Color', 'string', 'Color'),
              ('Count', 'number', 'Count')]
    colors = ['BLUE' ,'GREEN', 'ORANGE', 'RED', 'YELLOW', 'N/A']
    colorToCount = dict(colorToCount)
    colorToCount['N/A'] = colorToCount.get('NONE',0)
    del colorToCount['NONE']
    rowData = [(c, colorToCount[c]) for c in colors]
    dtLineCount = gviz_api.DataTable(schema, rowData)
    return dtLineCount

#############################
# We use a hack to make each bar it's own color
def makeColorCountsGoogleTableCustom(colorToCount):
    #BLUE, GREEN, ORANGE, RED, YELLOW, NONE
    schema = [('Color', 'string', 'Color'),
              ('CountBlue', 'number', 'Count'),
              ('CountGreen', 'number', 'Count'),
              ('CountOrange', 'number', 'Count'),
              ('CountRed', 'number', 'Count'),
              ('CountYellow', 'number', 'Count'),
              ('CountNone', 'number', 'Count'),
              ]
    colors = ['BLUE' ,'GREEN', 'ORANGE', 'RED', 'YELLOW', 'N/A']
    colorToOffset = dict((k,i+1) for i,k in enumerate(colors))
    def makeRowVec(color, value):
        numFields = len(colors) + 1
        data = [0] * numFields
        data[0] = color
        data[colorToOffset[color]] = value
        return data

    colorToCount = dict(colorToCount)
    colorToCount['N/A'] = colorToCount.get('NONE',0)
    del colorToCount['NONE']
    rowData = [makeRowVec(c, colorToCount[c]) for c in colors]
    dtLineCount = gviz_api.DataTable(schema, rowData)
    return dtLineCount

###############################
# Get Time Series of Hot Car Report Count and Daily High Temperature
def makeHotCarTimeSeries(db):
    hotCarDict = getHotCarToReports(db)
    reports = [r for rl in hotCarDict.itervalues() for r in rl]
    reportDates = [r['time'].date() for r in reports]
    dateCounts = Counter(reportDates)

    firstDate = min(reportDates)
    today = date.today()
    numDays = (today-firstDate).days + 1
    days = [firstDate + timedelta(days=i) for i in range(numDays)]

    dailyTemps = dict(getDailyTemps(db, firstDate, today))
    assert(len(dailyTemps) == len(days))

    schema = [('date', 'date', 'date'),
              ('count', 'number', 'Hot Car Reports'),
              ('temp', 'number', 'DC Temperature')]
    rowData = [(d, dateCounts.get(d,0), int(dailyTemps.get(d,0)) ) for d in days]
    dtDateCounts = gviz_api.DataTable(schema, rowData)
    return dtDateCounts

################################################
# Get the max temperatue for each day between
# firstDay and lastDay.
# lastDay should be no greater than today.
def getDailyTemps(db, firstDay, lastDay = None):

    W = hotCars.getWundergroundAPI()
    today = date.today()
    if lastDay is None:
        lastDay = today

    lastDay = min(lastDay, today)
    toDateTime = lambda d: datetime(d.year, d.month, d.day)

    # Extract temperatures from database. Convert datetimes to dates.
    allTemps = db.temperatures.find()
    dayToTemp = dict((doc['_id'].date(), doc['maxTemp']) for doc in allTemps)

    def genDayTemps():
        numDays = (lastDay - firstDay).days
        dateGen = (firstDay + timedelta(days=i) for i in xrange(numDays+1))
        lastTemp = 0
        for d in dateGen:
            maxTemp = dayToTemp.get(d, None)
            if maxTemp is None or d == today:
                # Get the temperature from the WundergroundAPI.
                wdata = W.getHistory(d, zipcode=20009, sleep=True)
                dailySummary = wdata.get('dailysummary', [])
                dailySummary = dailySummary[0] if dailySummary else {}
                maxTemp = float(dailySummary.get('maxtempi', lastTemp)) # Set to yesterday's temp if it's not available
                dt = toDateTime(d)
                db.temperatures.update({"_id" : dt}, {"$set" : {'maxTemp' : maxTemp}}, upsert=True)
            lastTemp = maxTemp
            yield (d, maxTemp)

    return  list(genDayTemps())


