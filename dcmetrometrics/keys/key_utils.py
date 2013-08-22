class MissingKeyError(Exception):
    pass

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

def keyModuleError():
    """
    Raise a RuntimeError due to a missing keys module.
    """

    msg = \
    """

    Could not import dcmetrometrics.keys module because the file is missing
    or is malformed.

    You must create the keys module using the provided template:

       cp dcmetrometrics/keys/keys_default.py dcmetrometrics/keys/keys.py

    For more information, see:
        https://github.com/LeeMendelowitz/DCMetroMetrics/wiki/API-Keys

    """
    raise RuntimeError(msg)
