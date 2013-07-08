import hotCars
import dbUtils
from operator import itemgetter
from collections import defaultdict, Counter
import gviz_api
import metroEscalatorsWeb
from twitter import TwitterError
from datetime import datetime, date, timedelta

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

def getAllHotCarData():
    db = dbUtils.getDB()

    # Car number to reports
    hotCarToReports = hotCars.getAllHotCarReports(db)

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
    # Make a DataTable with this data
    schema = [('carNum', 'string', 'Car'),
              ('line', 'string', 'Line'),
              ('numReports', 'number', 'Num. Reports'),
              ('lastReportTime', 'datetime', 'Last Report Time'),
              ('lastReport', 'string', 'Last Report'),
              ('allReports', 'string', 'All Reports')]
    rowData = []
    for d in hotCarData.itervalues():
        lastReport = d['lastReport']
        row = [makeHotCarLink(d['carNum']),
               metroEscalatorsWeb.lineToColoredSquares(d['colors']),
               len(d['reports']),
               d['lastReportTime'],
               recToLinkHtml(lastReport, lastReport['handle']),
               tweetLinks(d['reports'])]
        rowData.append(row)
    dtHotCars = gviz_api.DataTable(schema, rowData)
    return dtHotCars

def getHotCarDataByUser():
    db = dbUtils.getDB()

    # Car number to reports
    hotCarToReports = hotCars.getAllHotCarReports(db)

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

def hotCarByUserGoogleTable():

    userHotCarData = getHotCarDataByUser()
    
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
               metroEscalatorsWeb.lineToColoredSquares(d['lines']),
               d['lastReportTime'],
               tweetLinks(d['reports'])]
        rowData.append(row)
    dtHotCarsByUser = gviz_api.DataTable(schema, rowData)
    return dtHotCarsByUser

# Get web page data for a single hot car
def getHotCarData(carNum):

    db = dbUtils.getDB()

    # Get all hot car reports for this car num
    reports = hotCars.getHotCarReportsForCar(db, carNum)

    # Get the tweet embedding html. Cache the html if it does not exist
    for report in reports:
        tweetId = int(report['tweet_id'])
        tweetData = db.hotcars_tweets.find_one(tweetId)
        embed_html = ''
        if 'embed_html' not in tweetData:
            T = hotCars.getTwitterAPI()
            try:
                embedding = T.GetStatusOembed(tweetId, hide_thread=False, omit_script=True, align='left')
                embed_html = embedding['html']
                db.hotcars_tweets.update({'_id' : tweetId}, {'$set' : {'embed_html' : embed_html}})
            except TwitterError as e:
                msg = 'Tweet Id: %i'%tweetId +\
                      '\nCaught Twitter error: %s'%(str(e))
                print msg

                # If the tweet does not exist, add a field saying so
                code = e.args[0][0].get('code', 0)
                if code == 34:
                    db.hotcars_tweets.update({'_id' : tweetId}, {'$set' : {'exists' : False}})
        else:
            embed_html = tweetData['embed_html']
        report['embed_html'] = embed_html

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
# Get number of reports per day
def makeReportTimeSeries():
    db = dbUtils.getDB()
    hotCarDict = hotCars.getAllHotCarReports(db)
    reports = [r for rl in hotCarDict.itervalues() for r in rl]
    reportDates = [r['time'].date() for r in reports]
    dateCounts = Counter(reportDates)

    firstDate = min(reportDates)
    today = date.today()
    numDays = (today-firstDate).days + 1
    days = [firstDate + timedelta(days=i) for i in range(numDays)]

    schema = [('date', 'date', 'date'),
              ('count', 'number', 'count')]
    rowData = [(d, dateCounts.get(d,0)) for d in days]
    dtDateCounts = gviz_api.DataTable(schema, rowData)
    return dtDateCounts
