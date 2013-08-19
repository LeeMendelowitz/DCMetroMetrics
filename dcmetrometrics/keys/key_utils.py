from ..common import MissingKeyError

class TwitterKeyError(MissingKeyError):
    pass

class TwitterKeys(object):
    @classmethod
    def checkKeys(cls):
        """
        Check that the twitter keys have been properly set.
        """
        req = ['consumer_key', 'access_token',
               'consumer_secret', 'access_token_secret']
        for k in req:
            val = getattr(cls, k, None)
            if (not val) or (not isinstance(val, str)):
                msg = 'Twitter Keys {name} attribute {attr} is not properly set. Check your keys.py'
                msg = msg.format(name = cls.__name__, attr=k)
                raise TwitterKeyError(msg)
    @classmethod
    def isSet(cls):
        req = ['consumer_key', 'access_token',
               'consumer_secret', 'access_token_secret']
        keysAreSet = True
        for k in req:
            val = getattr(cls, k, None)
            if (not val) or (not isinstance(val, str)):
                keysAreSet = False
        return keysAreSet
                
