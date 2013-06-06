import hotCars

def makeTwitterUrl(handle, statusId):
    s = 'https://www.twitter.com/{handle}/status/{statusId}'
    return s.format(handle=handle, statusId=statusId)

def tweetLinks(records):
    
    def getLinkHtml(rec):
        handle = rec['handle']
        tweetId = rec['tweet_id']
        url = makeTwitterUrl(handle, tweetId)
        s = '<a href="{url}">{handle}</a>'
        return s.format(url=url, handle=handle)

    linkHtmls = [getLinkHtml(rec) for rec in records]
    linkString = ' '.join(linkHtmls)
    return linkString



