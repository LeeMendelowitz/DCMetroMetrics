import pymongo
from keys import HotCarKeys as keys
import tweepy
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
def preprocessText(text):
    pp = re.sub('(\d+)', ' \\1 ', text).upper()
    return pp

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
                     'ORANGE' : ['OR'],
                     #'SILVER' : ['SL']
                   }
    for c in colorToWords:
        colorToWords[c].append(c)
    wordToColor = dict((w,k) for k,wlist in colorToWords.iteritems() for w in wlist)
    colors = (wordToColor.get(w, None) for w in text.split())
    colors = [c for c in colors if c is not None]
    return colors

#######################################
def tick(db, tweetLive = False):
    curTime = datetime.now()
    sys.stderr.write('Running HotCar Tick. %s\n'%(str(curTime)))
    sys.stderr.write('Tweeting Live: %s\n'%str(tweetLive))
    initAppState(db, curTime)
    appState = next(db.hotcars_appstate.find({'_id' : 1}))

    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)
    T = tweepy.API(auth)

    # Get the latest tweets about WMATA hotcars
    tweets = list(T.search('wmata hotcar',
                   rpp=100,
                   since_id = appState['lastTweetId'],
                   result_type = 'recent'))

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

    for tweet in filteredTweets:
        hotCarData = getHotCarData(tweet)
        updateDBFromTweet(db, tweet, hotCarData)
        response = genResponseTweet(tweet, hotCarData)
        if response:
            print 'Response for Tweet %i'%tweet.id, response
            if tweetLive:
                T.update_status(response, in_reply_to_status_id = tweet.id)
                 
    # Update the app state
    maxTweetId = appState['lastTweetId']
    if filteredTweets:
        maxTweetId = max(tweet.id for tweet in filteredTweets)
    update = {'_id' : 1, 'lastRunTime': curTime, 'lastTweetId': maxTweetId}
    query = {'_id' : 1}
    db.hotcars_appstate.find_and_modify(query=query, update=update, upsert=True)

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
    doc = {'_id' : tweet.id,
           'user_id' : tweet.from_user_id,
           'text' : tweet.text,
           'time' : tweet.created_at}
    db.hotcars_tweets.insert(doc)

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
        sys.stderr.write('NOT updating hotcars collection with tweet %i:\n\t%s\n'%(tweet.id, tweet.text))

########################################
# Generate reponse tweet
def genResponseTweet(tweet, hotCarData):
    carNums = hotCarData['cars']
    colors = hotCarData['colors']
    tweetValid = len(carNums)==1 and carNums[0][0] in '123456'
    if not tweetValid:
        return None

    user = tweet.from_user
    color = colors[0] if len(colors) == 1 else ''
    car = carNums[0]
    if color:
        msg = '@wmata {color} Car {car} is a #WMATAHotCar HT @{user}'.format(color=color, car=car, user=user)
    else:
        msg = '@wmata Car {car} is a #WMATAHotCar HT @{user}'.format(color=color, car=car, user=user)
    return msg
