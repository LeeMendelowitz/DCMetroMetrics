"""
hotcars.hotCars

Utility functions for the HotCars app

"""
import pymongo
import sys
import re
from datetime import datetime, timedelta, date
from dateutil import tz
from dateutil.tz import tzlocal
import time
from collections import defaultdict, Counter
from operator import itemgetter
from mongoengine import DoesNotExist, NotUniqueError

from . import models
from .twitter_api import getTwitterAPI
from .process_tweets import (preprocessText, getHotCarDataFromText,
        uniqueTweets, tweetIsValidReport, isRetweet)
from .models import (HotCarAppState, HotCarTweet, HotCarTweeter, HotCarReport, CarsForbiddenByMention, Temperature)

from ..third_party.twitter import TwitterError
from ..common.globals import WWW_DIR
from ..common import twitterUtils
from ..common import dbGlobals
from ..common.JSONifier import JSONWriter
from ..common.metroTimes import utcnow, toLocalTime, UTCToLocalTime, tzutc

import logging
logger = logging.getLogger('HotCarApp')
logger.setLevel(logging.DEBUG)
    
ME = 'MetroHotCars'.upper()

# Words which are not allowed in tweets which mention MetroHotCars
mentions_forbidden_words = set(w.upper() for w in ['cold', 'cool'])

def getHotCarUrl(carNum):
    url = 'http://www.dcmetrometrics.com/hotcars/detail/{carNum}'.format(carNum=carNum)
    return url

def getWundergroundAPI():
    from .wundergroundAPI import WundergroundAPI
    try:
        # Import may fail if keys/keys.py has not been created.
        from ..keys import WUNDERGROUND_API_KEY
    except Exception as e:
        # Import of keys/keys.py failed - set key to None.
        WUNDERGROUND_API_KEY = None
    return WundergroundAPI(WUNDERGROUND_API_KEY, callsPerMinute=10)



#######################################
def tick(tweetLive = False):

    dbGlobals.connect()
    curTime = utcnow()
    curTimeLocal = toLocalTime(curTime)
    logger.info('Running HotCar Tick. %s\n'%(str(curTimeLocal)))
    logger.info('Tweeting Live: %s\n'%str(tweetLive))
            
    appState = HotCarAppState.get()
    lastTweetId = appState.lastTweetId if appState.lastTweetId else 0

    T = getTwitterAPI()

    logger.info('last tweet id: %i\n'%lastTweetId)

    # Generate reponse tweets for any tweets which have not yet been acknowledged
    tweetResponses = []
    unacknowledged = list(HotCarTweet.objects(acknowledged = False))
    logger.info('Found %i unacknowledged tweets\n'%(len(unacknowledged)))
    for tweet in unacknowledged:
        response = genResponseTweet(tweet.handle, getHotCarDataFromText(tweet.text))
        tweetResponses.append((tweet.tweet_id, response))

    # Remove any tweets returned by Twitter search which mention ME. These
    # will be collected by getMentions, which is careful
    # about what cars are allowed to be reported by mention instead of hash tag.
    def tweetMentionsMe(tweet):
        mentions = (u.screen_name.upper() for u in tweet.user_mentions)
        return ME in mentions

    # Get the latest tweets about WMATA hotcars. Ignore tweets which
    # mention MetroHotCars, as these will be processed by getMentions
    queries = ['wmata hotcar', 'wmata hot car', 'wmata hotcars', 'wmata hot cars']
    tweets = []
    for q in queries:
        queryResult = T.GetSearch(q, count=100, since_id = lastTweetId, result_type='recent', include_entities=True)
        tweets.extend(t for t in queryResult if not tweetMentionsMe(t))

    # Find the max tweet id seen through twitter search
    maxTweetId = max([t.id for t in tweets]) if tweets else 0
    maxTweetId = max(maxTweetId, lastTweetId)

    # Get tweets which mention MetroHotCars
    tweets.extend(getMentions(curTime=curTime))

    # Make a set of unique tweets
    tweets = uniqueTweets(tweets)
    logger.info('Twitter search returned %i unique tweets\n'%len(tweets))

    def filterPass(t):
        """ Only consider reports that are not retweets and
        not tweets from MetroHotCars.
        """
        # Reject retweets
        if isRetweet(t):
            return False

        # Ignore tweets from self
        if t.user.screen_name.upper() == ME.upper():
            return False

        return True

    filteredTweets = [t for t in tweets if filterPass(t)]
    tweetIds = set(t.id for t in filteredTweets)

    # Make sure we have a set of unique tweets.
    assert(len(tweetIds) == len(filteredTweets))

    logger.info('Filtered to %i tweets after removing re-/self-tweets\n'%len(filteredTweets))

    tweetData = [(t, getHotCarDataFromText(t.text)) for t in filteredTweets]
    tweetData = [(t, hcd) for t,hcd in tweetData if tweetIsValidReport(t, hcd)]
    tweetData = filterDuplicateReports(tweetData)
    tweetIds = set(t.id for t,hcd in tweetData)

    logger.info('Filtered to %i tweets after removing invalid and duplicate reports\n'%len(tweetData))
    logger.info('Have %i tweets about hot cars\n'%len(tweetData))

    for tweet, hotCarData in tweetData:
        validTweet = tweetIsValidReport(tweet, hotCarData)
        if not validTweet:
            continue

        updated = updateDBFromTweet(tweet, hotCarData)

        # If we updated the database with data on this tweet,
        # generate a response tweet
        if updated:
            user = tweet.user.screen_name
            response = genResponseTweet(user, hotCarData)
            tweetResponses.append((tweet.id, response))

    # Update the app state
    HotCarAppState.update(lastRunTime = curTime, lastTweetId = maxTweetId)
    
    # Tweet Responses
    for tweetId, response in tweetResponses:

        if response is None:
            continue

        logger.info('Response for Tweet %i: %s\n'%(tweetId, response))

        if tweetLive:

            try:

                T.PostUpdate(response, in_reply_to_status_id = tweetId)

                # Update the acknowledgement status of the tweet
                tweet_doc = HotCarTweet.objects(tweet_id = tweetId).get()
                tweet_doc.acknowledged = True
                tweet_doc.save()

            except TwitterError as e:

                logger.error('Caught TwitterError when trying to acknowledge tweet %i!: %s'%(tweetId, str(e)))
            
            except DoesNotExist as e:
                logger.error('Caught DoesNotExist when trying to mark tweet %i as acknowledged!:\n%s'%(tweetId, str(e)))

    # Write hotcar json file for website if data has changed
    if tweetResponses:
        logger.info('Writing json data.')
        jwriter = JSONWriter(WWW_DIR)
        jwriter.write_hotcars()


##################################################
# Get the UTC time of the tweet, from sec since epoch
# in localtime. The epoch is midnight 1/1/1970 in UTC.
def makeUTCDateTime(secSinceEpoch):
    t = time.gmtime(secSinceEpoch)
    dt = datetime(t.tm_year, t.tm_mon, t.tm_mday,
                  t.tm_hour, t.tm_min, t.tm_sec).replace(tzinfo=tzutc)
    return dt


def updateDBFromTweet(tweet, hotCarData):
    """
    Create a HotCarTweet document, HotCarTweeter document,
    and HotCarReport document.

    tweet: The tweet (from python-twitter)
    hotCarData: The data extracted from the tweet.
    """

    #logger.info('hotcars_tweets has %i docs\n'%(db.hotcars_tweets.count()))
    logger.info('Updating hotcar_tweets collection with tweet %i\n'%tweet.id)
    tweetText = tweet.text.encode('utf-8', errors='ignore')

    # Check if this is a duplicate, and abort if so.
    try:
        tweet = models.HotCarTweet.objects(pk = tweet.id).get()
        logging.info('No update made. Tweet %i is a duplicate.\n'%tweet.id)
        return False
    except DoesNotExist:
        pass
 

    # Get the HTML Embedding of the tweet. This may fail if the user
    # immediately deleted the tweet.
    T = getTwitterAPI()
    embed_html = None
    try:
        embedding = T.GetStatusOembed(tweet.id, hide_thread=False, omit_script=True, align='left')
        embed_html = embedding['html']
    except TwitterError as e:
        msg = 'Tweet Id: %i'%tweetId +\
              '\nCaught Twitter error when trying to get Status Oembed: %s\n'%(str(e))
        logger.error(msg)

    # Save the tweet.
    tweet_doc = HotCarTweet(tweet_id = tweet.id,
                            acknowledged = False,
                            embed_html = embed_html,
                            text = tweetText,
                            time = makeUTCDateTime(tweet.created_at_in_seconds),
                            user_id = tweet.user.id,
                            handle = tweet.user.screen_name)
    try:
        tweet_doc.save()
    except NotUniqueError:
        logging.info('No update made. Tweet %i is a duplicate.'%tweet.id)    
        return False

    # Update informatino about the twitter user who reported the car.
    HotCarTweeter.update(tweet.user.id, tweet.user.screen_name)

    # Update hotcars collection
    carNums = hotCarData['cars']
    colors = hotCarData['colors']
    carNum = int(carNums[0])
    color = colors[0] if colors and len(colors)==1 else None

    hot_car_report_doc = HotCarReport(car_number = carNum,
                                      tweet = tweet_doc,
                                      time = makeUTCDateTime(tweet.created_at_in_seconds),
                                      color = color)
    hot_car_report_doc.denormalize()

    try:
        hot_car_report_doc.save()
        updated = True

    except NotUniqueError:
        # A hot car report already exists for this tweet. Retrieve it and denormalize it.
        logger.warning("Tried to save HotCarReport document for tweet %i, but a document for this car already exists."%tweet.id)
        hot_car_report_doc = HotCarReport.objects(tweet = tweet_doc).get()
        hot_car_report_doc.denormalize()
        hot_car_Report_doc.save()
        updated = False

    return updated




def filterDuplicateReports(tweetData):
    """
    Remove tweets which are duplicate reports.
    A tweet is a duplicate report if:
    #
    1. It mentions another user
    who previously reported the same hot car within the last
    30 days.
    #
    2. The same user reported the same hot car within the last
    30 days. Some users may repeated talk about the same car.
    #
    tweetData: List of (tweet, hotCarData) tuples
    """
 
    # Build a dictionary from car number to the reporting users/times.
    # This includes all previous reports.
    hotCarReportDict= defaultdict(list)

    def doc_to_data(doc):
        """Extract data from a HotCarReport document to be used locally"""
        return { 'car_number': doc.car_number,
                 'tweet_id': doc.tweet.tweet_id,
                 'time' : doc.time,
                 'user_id' : doc.tweet.user.user_id }

    # Collect some fields from exists hot car reports.
    doc_data = (doc_to_data(doc) for doc in HotCarReport.iter_reports())
    for dd in doc_data:
        hotCarReportDict[dd['car_number']].append(dd)


    # Add the current batch of tweets to the hotCarReportDict
    for tweet, hotCarData in tweetData:
        cars = hotCarData['cars']
        assert(len(cars)==1)
        carNumber = cars[0]
        data = {'car_number' : carNumber,
                'time' : makeUTCDateTime(tweet.created_at_in_seconds),
                'tweet_id' : tweet.id,
                'user_id' : tweet.user.id
               }                

        hotCarReportDict[carNumber].append(data)

    filteredTweetData = []
    for tweet, hotCarData in tweetData:
        tweetTime = makeUTCDateTime(tweet.created_at_in_seconds)
        timeCutoff = tweetTime - timedelta(days=30)
        user_id = tweet.user.id
        screen_name = tweet.user.screen_name
        tweet_id = tweet.id
        assert(len(cars)==1)
        carNumber = hotCarData['cars'][0]
        otherReports = [d for d in hotCarReportDict[carNumber] if d['tweet_id'] != tweet_id and
                                                                  d['time'] > timeCutoff]

        # Check if this car was already reported by the user within 30 days
        prevSelfReports = sum(1 for d in otherReports if d['user_id'] == user_id)
        
        # Check if this car was already reported by another user mentioned in this tweet
        mentionUserIds = set(u.id for u in tweet.user_mentions)
        if tweet.in_reply_to_user_id is not None:
            mentionUserIds.add(tweet.in_reply_to_user_id)

        otherUserReports = sum(1 for d in otherReports if (d['user_id'] in mentionUserIds)
                                                          and (d['time'] < tweetTime))
        if (prevSelfReports > 0):
            logger.info('Skipping Tweet %i by %s on car %i because there is a previous self-report' \
                      ' in last 30 days\n'%(tweet_id, screen_name, carNumber))
            continue
        if (otherUserReports > 0):
            logger.info('Skipping Tweet %i by %s on car %i because it mentions another report ' \
                      ' from last 30 days\n'%(tweet_id, screen_name, carNumber))
            continue
        filteredTweetData.append((tweet, hotCarData))

    return filteredTweetData

########################################
# Generate reponse tweet
def genResponseTweet(handle, hotCarData):
    carNums = hotCarData['cars']
    colors = hotCarData['colors']

    normalize = lambda s: s[0].upper() + s[1:].lower()
    color = normalize(colors[0]) if len(colors) == 1 else ''
    car = carNums[0]

    if color:
        msg = '@wmata @MetroRailInfo {color} line car {car} is a #wmata #hotcar HT @{handle}'.format(color=color, car=car, handle=handle)
    else:
        msg = '@wmata @MetroRailInfo Car {car} is a #wmata #hotcar HT @{handle}'.format(car=car, handle=handle)

    # Add information about the number of reports for this hot car.
    numReports = HotCarReport.num_reports_for_car(int(car))
    carUrl = getHotCarUrl(car)

    if numReports > 1:
        msg = msg + '. Car reported {0} times. {1}'.format(numReports, carUrl)
    elif numReports == 1:
        msg = msg  + '. Car reported {0} time. {1}'.format(numReports, carUrl)

    return msg



def getForbiddenCarsByMention():
    """
    Check non-automated tweets made by MetroHotCars
    If MetroHotCars mentions a 4-digit car number,
    in a non-automated tweet,
    we forbid submissions of the same hot car number via
    menion for a 2-day period. 
   
    This is done to forbid duplicate reports if a user
    modifies or quotes the non-automated tweet.
   
    Returns a set of forbidden car numbers
    """

    appState = HotCarAppState.get()
    lastSelfTweetId = appState.lastSelfTweetId if appState.lastSelfTweetId else 0

    # Clean up any old forbidden car numbers (older than two days)
    CarsForbiddenByMention.remove_stale_docs()

    # Get any tweets by MetroHotCars since the lastSelfTweetId
    T = getTwitterAPI()
    selfTweets = T.GetUserTimeline(screen_name = ME, since_id = lastSelfTweetId, count = 200)
    maxTweetId = max(t.id for t in selfTweets) if selfTweets else 0
    maxTweetId = max(lastSelfTweetId, maxTweetId)

    def isAutomatedTweet(tweet):
        text = tweet.text.upper()
        pattern = "CAR \d{4} IS A #WMATA #HOTCAR HT"
        return (re.search(pattern, text) is not None)

    nonAutomatedTweets = [t for t in selfTweets if not isAutomatedTweet(t)] 

    # Get any car numbers in nonAutomatedTweet and forbid them from being
    # reported via mentions

    def getTimeCarPairs(tweet):
        hcd = getHotCarDataFromText(tweet.text)
        time = makeUTCDateTime(tweet.created_at_in_seconds)
        return [(time, n) for n in hcd['cars']]

    timeAndCarNums = [(time,carNum) for tweet in nonAutomatedTweets\
                                    for time,carNum in getTimeCarPairs(tweet)]

    # Add these car numbers to the hotcars_forbidden_by_mention database
    for time, carNum in timeAndCarNums:
        CarsForbiddenByMention.add(car_number = car_number, time = time)

    # Update the app state
    HotCarAppState.update(lastSelfTweetId = maxTweetId)

    # Return the list of tweetIds which are forbidden by mention
    return CarsForbiddenByMention.get_forbidden_cars()

def getMentions(curTime):
    """
    Search Twitter for tweets that mention MetroHotCars.
    This is rate limited, so perform every 90 seconds.

    Turning tweets from mentions into HotCar reports can be tricky, because
    a user may be quoting a tweet from MetroHotCars.

    For example, if MetroHotCars tweets "Car 1043 is a #wmata #hotcar. Car 1043 mentioned 5 times."
    a third user may say "WOW Car 1043 still isn't fixed! @MetroHotcars". This isn't a new report.
    This is why reporting cars with #wmata #hotcar without a mention is more reliable than by mention.
    """

    appState = HotCarAppState.get()
    lastMentionsCheckTime = appState.lastMentionsCheckTime
    if lastMentionsCheckTime is not None:
        lastMentionsCheckTime = lastMentionsCheckTime.replace(tzinfo=tzutc)
    lastMentionsTweetId = appState.lastMentionsTweetId if appState.lastMentionsTweetId else None
    doCheck = False

    if (lastMentionsCheckTime is None) or \
       (curTime - lastMentionsCheckTime) > timedelta(seconds=90.0):
       doCheck = True

    if not doCheck:
        return []
    
    T = getTwitterAPI() 
    mentions = T.GetMentions(include_entities = True, since_id = lastMentionsTweetId)
    maxMentionsTweetId = max(t.id for t in mentions) if mentions else 0
    maxMentionsTweetId = max(maxMentionsTweetId, lastMentionsTweetId)

    def hasForbiddenWord(t):
        text = t.text.upper()
        count = sum(1 for w in mentions_forbidden_words if w in text)
        return count > 0

    # Get car numbers which are forbidden to be submitted by mention
    forbiddenCarNumbers = getForbiddenCarsByMention()

    def tweetIsForbidden(tweet):
        carNums = getHotCarDataFromText(tweet.text)['cars']
        return any(carNum in forbiddenCarNumbers for carNum in carNums)

    mentions = [t for t in mentions if (not hasForbiddenWord(t)) and (not tweetIsForbidden(t))]

    # Update the appstate
    HotCarAppState.update(lastMentionsCheckTime = curTime,
        lastMentionsTweetId = maxMentionsTweetId)

    return mentions


###################################################################
# Code below is old and might be dead. TBD.
# Count the number of weekdays betweet datetimes t1 and t2
def countWeekdays(t1, t2):
    d1 = date(t1.year, t1.month, t1.day)
    d2 = date(t2.year, t2.month, t2.day)
    dt = d2 - d1
    numDays = (d2 - d1).days
    dateGen = (d1 + timedelta(days=i) for i in xrange(numDays+1))
    numWeekdays = sum(1 for d in dateGen if d.weekday() < 5)
    return numWeekdays

def summarizeReports(db, reports):
    numReports = len(reports)
    reports = sorted(reports, key = itemgetter('time'))
    firstReport = reports[0]
    firstReportTime = firstReport['time']
    lastReport = reports[-1]
    lastReportTime = lastReport['time']

    # Count the number of unique reporters
    tweetData = [db.hotcars_tweets.find_one({'_id' : r['tweet_id']}) for r in reports]
    users = set(t['user_id'] for t in tweetData)

    carNumbers = set(r['car_number'] for r in reports)
    numCars = len(carNumbers)

    # Color to Num Reports
    colorToCount = Counter(r['color'] for r in reports)

    # Series to Count
    seriesToCount = Counter(str(r['car_number'])[0] for r in reports)

    # Get the number of days between the first and last report
    timeDelta = (lastReportTime - firstReportTime)
    secondsPerDay = 3600.0*24
    numDays = timeDelta.total_seconds()/secondsPerDay
    numWeekDays = countWeekdays(firstReportTime, lastReportTime)
    dayDelta = timeDelta.days
    reportsPerDay = numReports/float(numDays)
    reportsPerWeekday = numReports/float(numWeekDays)
    res = {'numReports' : numReports,
           'numCars' : numCars,
           'reportsPerDay' : reportsPerDay,
           'reportsPerWeekday' : reportsPerWeekday,
           'numReporters' : len(users),
           'colorToCount' : colorToCount,
           'seriesToCount' : seriesToCount}
    return res
