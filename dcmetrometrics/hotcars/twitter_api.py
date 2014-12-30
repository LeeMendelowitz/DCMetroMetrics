"""
getTwitterAPI: Return the python_twitter
"""
from ..common import twitterUtils
from twitter import TwitterError

T = None
def getTwitterAPI():
    global T

    if T is None:
        from ..keys import HotCarKeys, MissingKeyError

        # Check that the HotCar Twitter API Keys have been set.
        if not HotCarKeys.isSet():
            msg = \
            """

            The HotCar App requires that the HotCarKeys be set.
            Check your keys.py.

            For more information, see:
            https://github.com/LeeMendelowitz/DCMetroMetrics/wiki/API-Keys

            """
            raise MissingKeyError(msg)

        T = twitterUtils.getApi(HotCarKeys)
    return T