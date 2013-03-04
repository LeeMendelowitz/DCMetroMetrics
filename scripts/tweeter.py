# Wrapper around tweepy api for making tweets
import tweepy
import keys
import sys

MAX_TWEET_LEN = 140

class TweetLengthError(Exception):
    pass

class Tweeter(object):

    def __init__(self, DEBUG=False):
        self.DEBUG = DEBUG
        self.consumer_key = keys.consumer_key
        self.access_token = keys.access_token
        self.auth = None # set by connect()
        self.api = None # set by connect()
        if not self.DEBUG:
            self.connect()

    def connect(self):
        self.auth = tweepy.OAuthHandler(self.consumer_key, keys.get_consumer_secret())
        self.auth.set_access_token(self.access_token, keys.get_access_token_secret())
        self.api = tweepy.API(self.auth)

    def tweet(self, msg):
        # Note: if the msg is too long, tweepy will raise a TweepError
        if len(msg) > MAX_TWEET_LEN:
            pass
            #raise TweetLengthError('Length: %i > %i'%(len(msg), MAX_TWEET_LEN))

        if self.DEBUG:
            sys.stdout.write(msg + '\n')
            return None

        res = self.api.update_status(msg)
        return res

    # This will attempt to clear all tweets that have been posted
    # CAUTION: THIS CANNOT BE UNDONE!
    def clearTimeline(self):
        sys.stdout.write('Continue? Y/N')
        sys.stdout.flush()
        l = sys.stdin.readline().strip()
        if l != 'Y':
            sys.stdout.write('Not clearing timeline.')
            return
        myTweets = self.api.user_timeline(count=200)
        sys.stderr.write('Deleting %i tweets'%len(myTweets))
        for t in myTweets:
            self.api.destroy_status(id=t.id)

    def getTimeline(self, **kwargs):
        myTweets = self.api.user_timeline(count=200, **kwargs)
        return myTweets
