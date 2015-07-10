"""Utilities for processing tweets to generate hot car reports
"""

##########################
import re

def preprocessText(tweetText):
  """
  Preprocess tweet text by padding 4 digit numbers with spaces,
  and converting all characters to uppercase
  """
  tweetText = tweetText.encode('ascii', errors='ignore')
  tweetText = tweetText.upper()

  # Remove any handles that are not @WMATA, to avoid mistaking
  # a 4 digit number in handle as a car number
  words = tweetText.split()
  words = [w for w in words if (w[0] != '@') or (w == '@WMATA')]
  tweetText = ' '.join(words)

  # Replace non-alphanumeric characters with spaces
  tweetText = re.sub('[^a-zA-Z0-9\s]',' ', tweetText)

  # Separate numbers embedded in words
  tweetText = re.sub('(\d+)', ' \\1 ', tweetText)

  # Make consecutive white space a single space
  tweetText = re.sub('\s+', ' ', tweetText)

  # Remove reference to 1000, 2000, ..., 6000 Series
  tweetText = re.sub('[1-6]000 SERIES', '', tweetText)

  return tweetText

def getCarNums(text):
  """
  Get 4 digit car numbers
  """
  nums = re.findall('\d+', text)
  validNums = [int(n) for n in set(s for s in nums if len(s)==4)]
  return validNums


#######################################
# Get colors mentioned from a tweet
# 
def getColors(text):
  """
  Extract line colors from text
  This assumes that the tweet text has already been preprocessed
  by removing hashtags and making all text uppercase.
  """

  colorToWords = { 'RED' : ['RD', 'RL', 'REDLINE'],
                   'BLUE' : ['BL', 'BLUELINE'],
                   'GREEN' : ['GR', 'GL', 'GREENLINE'],
                   'YELLOW' : ['YL', 'YELLOWLINE'],
                   'ORANGE' : ['OL', 'ORANGELINE']
                 }

  for c, colorWordList in colorToWords.iteritems():
      colorWordList.append(c) # Add the color itself to the word list
      colorToWords[c] = colorWordList

  wordToColor = dict((w,k) for k,wlist in colorToWords.iteritems() for w in wlist)
  words = text.split()
  colors = (wordToColor.get(w, None) for w in words)
  colors = [c for c in colors if c is not None]

  # Special handling of the silver line.
  # Be wary of "Silver Spring". It's tough, because
  # Spring Hill is an actual Silver Line station, so we may miss some
  # silver line tags.
  if 'SV' in words:
      colors.append('SILVER')
  if ('SILVER' in words) and\
     ("SPRING" not in words) and\
     ("SPRNG" not in words):
      colors.append('SILVER')

  colors = list(set(colors))

  return colors

def uniqueTweets(tweetList):    
  """
  Return a list of unique tweets from a list of tweets.
  """
  seen = set()
  unique = [t for t in tweetList if not (t.id in seen or seen.add(t.id))]
  return unique

def isRetweet(tweet):
  txt = tweet.text
  return (tweet.retweeted_status or ('MT' in txt) or ('RT' in txt))

def getHotCarDataFromText(text):
  """
  Get hot car data from text. Extract car numbers and line colors
  """
  pp = preprocessText(text)
  carNums = getCarNums(pp)
  colors = getColors(pp)
  return {'cars' : carNums,
          'colors' : colors } 

###########################################################
# Return True if we should store hot car data on this tweet
# and generate a twitter response
def tweetIsValidReport(tweet, hotCarData):
    """Return True if we should store hot car data on this tweet
     and generate a twitter response. A tweet is invalid if:

      - the tweet is from MetroHotCars OR
      - the tweet mentions multiple cars by number OR
      - the car is not a valid car number OR
      - the tweet mentions MBTA or BART
    """

    # Ignore tweets from self
    me = 'MetroHotCars'
    if tweet.user.screen_name.upper() == me.upper():
        return False

    # Ignore retweets
    if isRetweet(tweet):
        return False

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
                  '6' : (6000, 6183),
                  '7' : (7000, 7747)
                }

    if firstDigit not in carRanges:
        return False

    # Require the car to be a valid number
    minNum, maxNum = carRanges[firstDigit]
    carNumValid = carNumInt <= maxNum and carNumInt >= minNum
    if not carNumValid:
        return False

    # Check if the tweet has any forbidded words.
    excludedWords = ['MBTA', 'BART']
    excludedWords = [w.upper() for w in excludedWords]
    excludedWords = set(excludedWords)
    tweetText = preprocessText(tweet.text)
    tweetWords = tweetText.split()
    numExcluded = sum(1 for w in tweetWords if w in excludedWords)
    if numExcluded > 0:
        return False

    # The tweet is good!
    return True   