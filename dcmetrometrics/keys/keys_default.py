"""
This file is a template for storing the API Keys used
by this application.

Copy this file into keys.py, and replace the None values with
str values of your own keys.

Required Keys
=============
 - The EscalatorApp and the ElevatorApp require the WMATA_API_KEY to run.
 - The HotCarsApp requires the HotCarKeys to seach for hot car tweets and to live tweet.

Optional keys
=============
 - The EscalatorApp needs the MetroEscalatorKeys to live tweet, otherwise
   tweet messages will only be written to a log file.
 - The ElevatorApp needs MetroElevatorKeys to live tweet, otherwise
   tweet message will only be written to a log file.
 - The WebPageGeneratorApp needs the WundergroundAPI to include DC temperature
   history on the hotcars webpage, otherwise default temperature values are used.
"""

from .key_utils import *

class MetroEscalatorKeys(TwitterKeys):
    """
    Key for @MetroEscalators Twitter acccount
    """
    consumer_key =  None
    access_token = None
    consumer_secret = None
    access_token_secret = None

class MetroElevatorKeys(TwitterKeys):
    """
    Key for @MetroElevators Twitter acccount
    """
    consumer_key =  None
    access_token = None
    consumer_secret = None
    access_token_secret = None

class HotCarKeys(TwitterKeys):
    """
    Key for @MetroHotCars Twitter account
    """
    consumer_key = None
    consumer_secret = None
    access_token = None
    access_token_secret = None

WUNDERGROUND_API_KEY = None

WMATA_API_KEY = None
