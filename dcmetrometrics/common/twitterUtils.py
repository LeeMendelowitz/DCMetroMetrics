"""
common.twitterUtils

"""
import twitter
from twitter import TwitterError

TWITTER_TIMEOUT = 10

def getApi(keys):
    """
    Construct a Twitter API instance.
    """
    api = twitter.Api(consumer_key = keys.consumer_key,
                       consumer_secret = keys.consumer_secret,
                       access_token_key = keys.access_token,
                       access_token_secret = keys.access_token_secret,
                       cache = None,
                       requests_timeout = TWITTER_TIMEOUT)
    return api
