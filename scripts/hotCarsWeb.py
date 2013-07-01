import hotCars
import dbUtils
from operator import itemgetter
from collections import defaultdict
import gviz_api
import metroEscalatorsWeb

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

def formatTimeStr(dt):
    tf = '%m/%d/%y %H:%M'
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

def getHotCarData():
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
    schema = [('carNum', 'number', 'Car'),
              ('line', 'string', 'Line'),
              ('numReports', 'number', 'Num. Reports'),
              ('lastReportTime', 'datetime', 'Last Report Time'),
              ('lastReport', 'string', 'Last Report'),
              ('allReports', 'string', 'All Reports')]
    rowData = []
    for d in hotCarData.itervalues():
        lastReport = d['lastReport']
        row = [d['carNum'],
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
