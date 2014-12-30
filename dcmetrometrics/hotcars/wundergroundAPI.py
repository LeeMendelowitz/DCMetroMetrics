"""
hotcars.wundergroundAPI

Implementation of the WundergroundAPI. This is used by
web.hotcars to query the daily high temperature for Washington DC.

"""
from datetime import date, datetime, timedelta
from time import sleep as do_sleep
import requests

TIMEOUT = 10.0

class WundergroundError(Exception):
    pass

class WundergroundAPI(object):
    """
    Wrapper class around the WundergroundAPI.
    """

    baseUrl = "http://api.wunderground.com/api"

    def __init__(self, key, callsPerMinute=None):
        """
        key: API Key as a str. If key is None, all calls to API method will
             return no result.
        callsPerMinute: The maximum number of callsPerMinute to enforce
        """
        if not isinstance(key, str) and key is not None:
            raise TypeError('key must be a str or None.')
        self.key = key if key else None
        self.callsPerMinute = callsPerMinute
        if callsPerMinute is not None and callsPerMinute <= 0:
            raise ValueError('callsPerMinute must be non-negative')

        self.enforceRateLimit = not (callsPerMinute is None)
        self.callTimes = []

    def _buildUrl(self, query, **kwargs):
        """
        Build the full request url by including the base url,
        the API key, and the query.
        """
        query = "{base}/{key}/" + query
        kwargs['base'] = self.baseUrl
        kwargs['key'] = self.key
        url = query.format(**kwargs)
        return url  

    def _request(self, url, sleep=False):
        """
        Make JSON request to the specified URL.
        Return the parsed JSON result.

        Raise a WundergroundError if the request fails or if the 
        Wunderground API returns an error.

        If sleep is True and the rate limit is enforced,
        then sleep before making a call which would exceed the rate limit
        """

        if not self._checkRateLimit(sleep):
            raise WundergroundError('Rate limit would be exceeded with this call.')

        if self.enforceRateLimit:
            self.callTimes.append(datetime.now())

        r = requests.get(url, timeout = TIMEOUT)
        if r.status_code != requests.codes.ok:
            msg = 'RequestError! URL=%s, StatusCode=%i'%(r.url, r.status_code)
            raise WundergroundError(msg)
        res = r.json()
        response = res['response']
        error = response.get('error', None)
        if error is not None:
            raise WundergroundError(str(error))
        return res

    def _checkRateLimit(self, sleep=False):
        """
        Check if a request will exceed the rate limit.
        If sleep is True, sleep until it is safe to make the call, if necessary.
        Return True if it is safe to make the call.
        Return False otherwise.
        """
        if not self.enforceRateLimit:
            return True

        # Clean up the callTimes which are more than a minute old
        now = datetime.now()
        minTime = now - timedelta(minutes=1)
        self.callTimes = [t for t in self.callTimes if (t >= minTime)]

        if len(self.callTimes) < self.callsPerMinute:
            return True
        elif not sleep:
            return False
        minCallTime = min(self.callTimes)
        nextCallTime = minCallTime + timedelta(minutes=1)
        sleepSeconds = (nextCallTime - now).total_seconds()
        if sleepSeconds > 0:
            #print 'Sleeping %.2f seconds'%sleepSeconds
            do_sleep(sleepSeconds)
        return True
    
    def getHistory(self, d, zipcode, sleep=False): 
        """ 
        Get the daily history for zip code d on date d
        """
        query_template = "history_{dateStr}/q/{zipcode}.json"

        if self.key is None:
            return {}

        if not isinstance(d, date):
            raise TypeError("d must be a datetime.date instance")
        if not isinstance(zipcode, str):
            zipcode = str(zipcode)
        if len(zipcode) != 5:
            raise TypeError("zipcode must be 5 digits")
        dateStr = d.strftime("%Y%m%d")
        query = self._buildUrl(query_template, dateStr=dateStr, zipcode=zipcode)
        res = self._request(query, sleep=sleep)
        history = res['history']
        return history
