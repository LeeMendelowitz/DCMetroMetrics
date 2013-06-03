import pymongo
from keys import HotCarKeys as keys
import tweepy
from tweepy import TweepError
import sys
import re
from datetime import datetime

##########################
def initAppState(db, curTime):
    if db.hotcars_appstate.count() == 0:
        doc = {'_id' : 1,
               'lastRunTime' : curTime,
               'lastTweetId' : 0}
        db.hotcars_appstate.insert(doc)

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

def getTweepyAPI():
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    T = tweepy.API(auth)
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

    T = getTweepyAPI()

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
        res = T.search(q,
                   rpp=100,
                   since_id = lastTweetId,
                   result_type = 'recent')
        tweets.extend(t for t in res)
    tweets = uniqueTweets(tweets)

    isRetweet = lambda t: len(t.text) >= 2 and t.text[0:2] == 'RT'
    def filterPass(t):
        if isRetweet(t):
            return False

        # Ignore tweets from self
        me = 'MetroHotCars'
        if t.from_user.upper() == me.upper():
            return False

        return True

    retweets = [t for t in tweets if isRetweet(t)]
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
                T.update_status(response, in_reply_to_status_id = tweet.id)
            except TweepError as e:
                sys.stderr.write('Caught TweepError!: %s'%str(e))
                

########################################
# Get hot car data from a tweet
def getHotCarData(tweet):
    pp = preprocessText(tweet.text)
    carNums = getCarNums(pp)
    colors = getColors(pp)
    return {'cars' : carNums,
            'colors' : colors }

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

    doc = {'_id' : tweet.id,
           'user_id' : tweet.from_user_id,
           'text' : tweet.text,
           'time' : tweet.created_at}
    db.hotcars_tweets.insert(doc)
    updated = True

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
               'time' : tweet.created_at}
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
    user = tweet.from_user
    color = normalize(colors[0]) if len(colors) == 1 else ''
    car = carNums[0]
    if color:
        msg = '@wmata {color} Car {car} is a #WMATAHotCar HT @{user}'.format(color=color, car=car, user=user)
    else:
        msg = '@wmata Car {car} is a #WMATAHotCar HT @{user}'.format(color=color, car=car, user=user)
    return msg
