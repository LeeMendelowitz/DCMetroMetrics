import hotCars
import dbUtils
from operator import itemgetter

def makeTwitterUrl(handle, statusId):
    s = 'https://www.twitter.com/{handle}/status/{statusId:d}'
    return s.format(handle=handle, statusId=statusId)

def recToLinkHtml(rec, text=None):
    handle = rec['handle']
    if text is None:
        text = handle
    tweetId = int(rec['tweet_id'])
    url = makeTwitterUrl(handle, tweetId)
    s = '<a href="{url}">{text}</a>'
    return s.format(url=url, text=text)

def formatTimeStr(dt):
    tf = '%m/%d/%y %H:%M'
    return dt.strftime(tf)

def tweetLinks(records):
    linkHtmls = [recToLinkHtml(rec, str(i+1)) for i, rec in enumerate(records)]
    linkString = ' '.join(linkHtmls)
    return linkString

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
                 'lastReport' : reports[-1]}
        carNumToData[carNum] = data

    return carNumToData
