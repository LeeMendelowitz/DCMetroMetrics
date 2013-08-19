"""
common.twitterUtils

"""

from ..third_party import twitter
from twitter import TwitterError

def getApi(keys):
    """
    Construct a Twitter API instance.
    """
    api = twitter.Api(consumer_key = keys.consumer_key,
                       consumer_secret = keys.consumer_secret,
                       access_token_key = keys.access_token,
                       access_token_secret = keys.access_token_secret,
                       cache=None)
    return api
