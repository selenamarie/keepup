#!/usr/bin/env python

import tweepy
from BeautifulSoup import BeautifulSoup as parser
import urllib
import sys

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("followers", help="fetch follower ids and urls")
parser.add_argument("friends", help="fetch friend ids and urls")
parser.add_argument("output", help="file to write output to")
parser.parse_args()

consumer_key='12Jbo5GoDxd6dq6epffIQ'
consumer_secret='00rIgEhKD944U3vt5vZdh0fXO4hEmQWY7vPOuyN7E'

access_token='8859592-nEVysnaIw43LbNN9OozIfgrP4HOJM5BS2m0lIZwGM'
access_token_secret='bH1QJRDKTsYymq4HOqL6XZwNMO6lTQumBphwOYPdbs'

def detect_feeds_in_HTML(input_stream):
    """ examines an open text stream with HTML for referenced feeds.

    This is achieved by detecting all ``link`` tags that reference a feed in HTML.

    :param input_stream: an arbitrary opened input stream that has a :func:`read` method.
    :type input_stream: an input stream (e.g. open file or URL)
    :return: a list of tuples ``(url, feed_type)``
    :rtype: ``list(tuple(str, str))``
    """
    # check if really an input stream
    if not hasattr(input_stream, "read"):
        raise TypeError("An opened input *stream* should be given, was %s instead!" % type(input_stream))
    result = []
    # get the textual data (the HTML) from the input stream
    html = parser(input_stream.read())
    # find all links that have an "alternate" attribute
    feed_urls = html.findAll("link", rel="alternate")
    # extract URL and type
    for feed_link in feed_urls:
        url = feed_link.get("href", None)
        # if a valid URL is there
        if url:
            result.append(url)
    return result

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def friends(api):
""" Takes an API, returns an array of IDs of friends """
    return api.friends_ids()

def followers(api):
    return api.followers_ids()

def find_feed(user):
   u = user
   try:
       site = urllib.urlopen(u.url)
       tuples = detect_feeds_in_HTML(site)
       for t in tuples:
           html = parser(u.url, convertEntities=parser.HTML_ENTITIES).contents[0]
           if "comment" in t:
               next
           if "\"" in t: # an annoying typo in the html from a friend
               next
           if "http" in t:
               xml = parser(t, convertEntities=parser.HTML_ENTITIES).contents[0]
           else:
               myxml = html + t
               xml = parser(myxml, convertEntities=parser.HTML_ENTITIES).contents[0]
           print opml_outline_feed % {'title': u.name, 'html_url': html, 'xml_url': xml}
           break

   except Exception, err:
        sys.stderr.write('ERROR: %s in %s\n' % {str(err), u.url})
        pass

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
if args.followers:
    users = api.followers_ids()

if args.friends:
    users = api.friends_ids()

if args.output:
    sys.stdout = open(

opml_start = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.1">
<head>
<title>People who follow me</title>
</head>
<body>
<outline text="People who follow me" title="People who follow me">"""

opml_end = """</outline>
</body>
</opml>"""

opml_outline_feed = '<outline text="%(title)s" title="%(title)s" type="rss" version="RSS" htmlUrl="%(html_url)s" xmlUrl="%(xml_url)s" />'

print opml_start
# Do this lookup in chunks of 100 because of twitter API limitations
for c in chunks(users, 100):
    users = api.lookup_users(c)
    for u in users:
        if u.url:
           print "<!-- %s -->" % u.screen_name
           find_feed(u)

print opml_end
