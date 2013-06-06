import pymongo
from keys import HotCarKeys as keys
from twitter import TwitterError
import twitterUtils
import sys
import re
from datetime import datetime
import time
from collections import defaultdict


##########################
def initAppState(db, curTime):
    if db.hotcars_appstate.count() == 0:
        doc = {'_id' : 1,
               'lastRunTime' : curTime,
               'lastTweetId' : 0}
        db.hotcars_appstate.insert(doc)

    if db.hotcars_tweeters.count() == 0:
        initTweetersDB(db)

##########################
def initTweetersDB(db):

    # initialize the database of tweeters
    hotcarTweetIds = db.hotcars.distinct('tweet_id')
    tweeterIds = []
    for tweetId in hotcarTweetIds:
        rec = next(db.hotcars_tweets.find({'_id': tweetId}))
        tweeterId = rec['user_id']
        tweeterIds.append(tweeterId)
    sys.stderr.write('Looking up %i tweetIds\n'%len(tweeterIds))

    T = getTwitterAPI()
    numAdded = 0
    for twitterId in tweeterIds:
        res = T.get_user(twitterId)
        handle = res.screen_name
        doc = {'_id' : twitterId,
               'handle' : handle}
        if db.hotcars_tweeters.find({'_id' : twitterId}).count() == 0:
            db.hotcars_tweeters.insert(doc)
            numAdded += 1
    sys.stderr.write('Added %i docs to hotcars_tweeters collection\n'%numAdded)

#########################################
# Get all hot car reports for a given car
def getHotCarReportsForCar(db, carNum):
    carNumStr = str(carNum)
    query = {'car_number' : carNumStr}
    db.hotcars.ensure_index([('car_number',pymongo.ASCENDING),('time', pymongo.DESCENDING)])
    cursor = db.hotcars.find(query).sort('time', pymongo.DESCENDING)
    hotCarReports = list(cursor)
    return hotCarReports

#########################################
# Add text, user_id, handle fields to the record
def makeFullHotCarReport(db, rec):
    tweetId = rec['tweet_id']
    tweetRec = db.hotcars_tweets.find_one({'_id' : tweetId})
    rec['user_id'] = tweetRec['user_id']
    rec['text'] = tweetRec['text']
    tweeterRec = db.hotcars_tweeters.find_one({'_id' : tweetRec['user_id']})
    rec['handle'] = tweeterRec['handle']
    return rec
     

#########################################
def getAllHotCarReports(db):
    db.hotcars.ensure_index([('car_number',pymongo.ASCENDING),('time', pymongo.DESCENDING)])
    cursor = db.hotcars.find().sort('time', pymongo.DESCENDING)
    hotCarReportDict = defaultdict(list)
    for report in cursor:
        report = makeFullHotCarReport(db, report)
        hotCarReportDict[report['car_number']].append(report)
    return hotCarReportDict


##########################
# Preprocess tweet text by padding 4 digit numbers with spaces,
# and converting all characters to uppercase
def preprocessText(tweetText):
    tweetText = tweetText.encode('ascii', errors='ignore')
    tweetText = re.sub('[^a-zA-Z0-9\s]',' ', tweetText).upper()
    tweetText = re.sub('(\d+)', ' \\1 ', tweetText).upper()
    return tweetText

###########################
# Get 4 digit numbers
def getCarNums(text):
    nums = re.findall('\d+', text)
    validNums = [s for s in nums if len(s)==4]
    return validNums

#######################################
# Get colors mentioned from a tweet
def getColors(text):
    colorToWords = { 'RED' : ['RD'],
                     'BLUE' : ['BL'],
                     'GREEN' : ['GR'],
                     'YELLOW' : ['YL'],
                     'ORANGE' : [],
                     #'SILVER' : ['SL']
                   }
    for c in colorToWords:
        colorToWords[c].append(c)
    wordToColor = dict((w,k) for k,wlist in colorToWords.iteritems() for w in wlist)
    colors = (wordToColor.get(w, None) for w in text.split())
    colors = [c for c in colors if c is not None]
    return colors

T = None
def getTwitterAPI():
    global T
    if T is None:
        T = twitterUtils.getApi(keys)
    return T

###########################
# Return a list of unique tweets from a list of tweets
def uniqueTweets(tweetList):    
    seen = set()
    unique = []
    for t in tweetList:
        if t.id not in seen:
            seen.add(t.id)
            unique.append(t)
    return unique

#######################################
def tick(db, tweetLive = False):
    curTime = datetime.now()
    sys.stderr.write('Running HotCar Tick. %s\n'%(str(curTime)))
    sys.stderr.write('Tweeting Live: %s\n'%str(tweetLive))
    sys.stderr.flush()             
    initAppState(db, curTime)
    appState = next(db.hotcars_appstate.find({'_id' : 1}))
    lastTweetId = appState.get('lastTweetId', 0)

    T = getTwitterAPI()

    # Determine the last hot car tweet we saw, so we can search for
    # tweets that have occurred since
#    lastTweetId = 0
#    if db.hotcars_tweets.count() > 0:
#        sortParams = [('_id', pymongo.DESCENDING)]
#        doc = next(db.hotcars_tweets.find(sort=sortParams))
#        lastTweetId = doc['_id']
#
    sys.stderr.write('last tweet id: %i\n'%lastTweetId)
#    lastTweetId = 0
#    sys.stderr.write('Forcing last tweet id: %i\n'%lastTweetId)

    # Get the latest tweets about WMATA hotcars
    queries = ['wmata hotcar', 'wmata hot car']
    tweets = []
    for q in queries:
        res = T.GetSearch(q, count=100, since_id = lastTweetId, result_type='recent')
        tweets.extend(t for t in res)
    tweets = uniqueTweets(tweets)

    def filterPass(t):

        # Reject retweets
        if t.retweeted_status:
            return False

        # Ignore tweets from self
        me = 'MetroHotCars'
        if t.user.screen_name.upper() == me.upper():
            return False

        return True

    filteredTweets = [t for t in tweets if filterPass(t)]
    tweetIds = set(t.id for t in filteredTweets)
    assert(len(tweetIds) == len(filteredTweets))

    tweetResponses = []
    for tweet in filteredTweets:
        hotCarData = getHotCarData(tweet)
        validTweet = tweetIsValid(tweet, hotCarData)
        if not validTweet:
            continue

        updated = updateDBFromTweet(db, tweet, hotCarData)

        # If we updated the database with data on this tweet,
        # generate a response tweet
        if updated:
            response = genResponseTweet(tweet, hotCarData)
            if response is not None:
                tweetResponses.append((tweet, response))

    # Update the app state
    maxTweetId = max([t.id for t in filteredTweets]) if filteredTweets else 0
    maxTweetId = max(maxTweetId, lastTweetId)
    update = {'_id' : 1, 'lastRunTime': curTime, 'lastTweetId' : maxTweetId}
    query = {'_id' : 1}
    db.hotcars_appstate.find_and_modify(query=query, update=update, upsert=True)

    for tweet, response in tweetResponses:
        if response is None:
            continue
        sys.stderr.write('Response for Tweet %i: %s\n'%(tweet.id, response))
        if tweetLive:
            try:
                T.PostUpdate(response, in_reply_to_status_id = tweet.id)
            except TwitterError as e:
                sys.stderr.write('Caught TwitterError!: %s'%str(e))

########################################
# Get hot car data from a tweet
def getHotCarData(tweet):
    pp = preprocessText(tweet.text)
    carNums = getCarNums(pp)
    colors = getColors(pp)
    return {'cars' : carNums,
            'colors' : colors }

def makeUTCDateTime(secSinceEpoch):
    t = time.gmtime(secSinceEpoch)
    dt = datetime(t.tm_year, t.tm_mon, t.tm_mday,
                  t.tm_hour, t.tm_min, t.tm_sec)
    return dt
########################################
def updateDBFromTweet(db, tweet, hotCarData):

    sys.stderr.write('hotcars_tweets has %i docs\n'%(db.hotcars_tweets.count()))
    sys.stderr.write('Updating hotcar_tweets collection with tweet %i\n'%tweet.id)
    tweetText = tweet.text.encode('utf-8', errors='ignore')

    # Check if this is a duplicate, and abort if so.
    count = db.hotcars_tweets.find({'_id' : tweet.id}).count()
    if count > 0:
        sys.stderr.write('No update made. Tweet %i is a duplicate.\n'%tweet.id)
        updated = False
        return updated

    # Store the tweet
    # TO DO: Store the timestamp as a datetime representing UTC time

        
    doc = {'_id' : tweet.id,
           'user_id' : tweet.user.id,
           'text' : tweet.text,
           'time' : makeUTCDateTime(tweet.created_at_in_seconds)}
    db.hotcars_tweets.insert(doc)
    updated = True

    # Store the user information
    update = {'_id' : tweet.user.id,
           'handle' : tweet.user.screen_name}
    query = {'_id': tweet.user.id}
    db.hotcars_tweeters.find_and_modify(query=query, update=update, upsert=True)

    carNums = hotCarData['cars']
    colors = hotCarData['colors']

    # Only add tweet data to the hotcars collection if 
    # a single car is listed, and it appears to be a good car number
    tweetValid = len(carNums)==1 and carNums[0][0] in '123456'
    if tweetValid:
        sys.stderr.write('hotcars has %i docs\n'%(db.hotcars.count()))
        sys.stderr.write('Updating hotcars collection with tweet %i\n'%tweet.id)
        carNum = int(carNums[0])
        color = colors[0] if colors and len(colors)==1 else 'NONE'
        doc = {'tweet_id' : tweet.id,
               'car_number' : carNum,
               'color' : color,
               'time' : makeUTCDateTime(tweet.created_at_in_seconds)}
        db.hotcars.insert(doc)
    else:
        sys.stderr.write('NOT updating hotcars collection with tweet %i:\n\t%s\n'%(tweet.id, tweetText))

    return updated

###########################################################
# Return True if we should store hot car data on this tweet
# and generate a twitter response
def tweetIsValid(tweet, hotCarData):

    carNums = hotCarData['cars']

    # Require a single car to be named in the tweet
    if len(carNums) != 1:
        return False

    carNumStr = str(carNums[0])
    carNumInt = int(carNums[0])
    firstDigit = carNumStr[0]


    # Car ranges are from Wikipedia, inclusive
    carRanges = { '1' : (1000, 1299),
                  '2' : (2000, 2075),
                  '3' : (3000, 3289),
                  '4' : (4000, 4099),
                  '5' : (5000, 5191),
                  '6' : (6000, 6183)
                }

    if firstDigit not in carRanges:
        return False

    # Require the car to be a valid number
    minNum, maxNum = carRanges[firstDigit]
    carNumValid = carNumInt <= maxNum and carNumInt >= minNum
    if not carNumValid:
        return False

    # Check if the tweet has any forbidded words
    excludedWords = ['series'] # People may refer to 3000 series cars
    excludedWords = [w.upper() for w in excludedWords]
    excludedWords = set(excludedWords)
    tweetText = preprocessText(tweet.text)
    tweetWords = tweetText.split()
    numExcluded = sum(1 for w in tweetWords if w in excludedWords)
    if numExcluded > 0:
        return False

    # The tweet is good!
    return True

########################################
# Generate reponse tweet
def genResponseTweet(tweet, hotCarData):
    carNums = hotCarData['cars']
    colors = hotCarData['colors']
    tweetValid = len(carNums)==1 and carNums[0][0] in '123456'
    if not tweetValid:
        return None

    normalize = lambda s: s[0].upper() + s[1:].lower()
    user = tweet.user.screen_name
    color = normalize(colors[0]) if len(colors) == 1 else ''
    car = carNums[0]
    if color:
        msg = '@wmata {color} line car {car} is a #WMATAHotCar HT @{user}'.format(color=color, car=car, user=user)
    else:
        msg = '@wmata Car {car} is a #WMATAHotCar HT @{user}'.format(car=car, user=user)
    return msg
