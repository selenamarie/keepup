#!/usr/bin/env python

import tweepy
from BeautifulSoup import BeautifulSoup as parser
import urllib
import sys
import argparse
import ConfigParser
import os
import unicodedata

import socket
socket.setdefaulttimeout(10)

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

class OPML:

    def process_feeds(self, tuples, user):
       """ Take tuples from detect_feeds_in_HTML() and create an outline entry for opml
       """
       for t in tuples:
           html = parser(user.url, convertEntities=parser.HTML_ENTITIES).contents[0]

           # Ignore feeds for comments
           if "comment" in t:
               next

           # Ignore annoying typo in the html from a friend
           if "\"" in t:
               next

           # Convert relative URLs
           if "http" in t:
               xml = parser(t, convertEntities=parser.HTML_ENTITIES).contents[0]
           else:
               myxml = html + t
               xml = parser(myxml, convertEntities=parser.HTML_ENTITIES).contents[0]

           # If we've got something, rather than nothing, return a hash
           if xml:
               return {'title': user.name, 'html_url': html, 'xml_url': xml}
           else:
               return None

    def find_feed(self, user):
       """ Takes a twitter api User object, grabs URL and then searches for feeds
       """
       if user.url:
           try:
               site = urllib.urlopen(user.url)
               feed = self.process_feeds(detect_feeds_in_HTML(site), user)
               return feed

           except Exception, err:
                sys.stderr.write('ERROR: %(err)s in %(url)s\n' % {'err': str(err), 'url': user.url})
                pass
       else:
            return None

    def connect_api(self, args):
        auth = tweepy.OAuthHandler(args.consumer_key, args.consumer_secret)
        auth.set_access_token(args.access_token, args.access_token_secret)

        api = tweepy.API(auth)
        return api

    def extract_entity_urls(self, user):
        urls = []
        print user.__getstate__()
        try:
            if user.entities.url.urls:
                for u in user.entities.url.urls:
                    urls.append(u.url)
        except:
            return urls
        return urls

    def get_users(self, api, args):

        if args.followers:
            users = api.followers_ids()

        if args.friends:
            users = api.friends_ids()

        return users

    def get_feeds(self, api, users, args):
        feeds = []
        # TODO put these in a database
        # Need to associate with a user
        for c in chunks(users, args.chunks):
            users = api.lookup_users(c)
            feeds = [self.find_feed(u) for u in users]
        return feeds

    def get_feeds_from_entities(self, api, users, args):
        entity_urls = []
        for c in chunks(users, args.chunks):
            users = api.lookup_users(c)
            entities = [url for u in users for url in self.extract_entity_urls(u)]
        return entities

    def pick_title(self, args):
        if args.title:
            return args
        if args.followers and args.friends:
            args.title = "Friends and Followers"
        elif args.followers:
            args.title = "Followers"
        elif args.friends:
            args.title = "Friends"
        return args

    def unfollow(self, api, args):
        with open(args.to_unfollow) as f:
            people_to_unfollow = [x.strip() for x in f.readlines()]
        for person in people_to_follow:
            try:
                api.destroy_friendship(person)
            except:
                # tweepy.error.TweepError: [{u'message': u"You've already requested to follow Pia_Gen", u'code': 160}]
                error = tweepy.error.TweepError
                print error

    def follow_women(self, api, args):
        with open(args.to_follow) as f:
            people_to_follow = [x.strip() for x in f.readlines()]
        for person in people_to_follow:
            try:
                api.create_friendship(person)
            except:
                # tweepy.error.TweepError: [{u'message': u"You've already requested to follow Pia_Gen", u'code': 160}]
                error = tweepy.error.TweepError
                print error

    def find_women(self, api, args):
        users = self.get_users(api, args)
        userids = []

        for c in chunks(users, args.chunks):
            users = api.lookup_users(c)

            for user in users:
                name = unicodedata.normalize('NFKD', user.name).encode('ascii','ignore')
                screen_name = unicodedata.normalize('NFKD', user.screen_name).encode('ascii','ignore')
                print ','.join([screen_name, name])

    def update_list(self, api, args):
        with open(args.update_list) as f:
            people_to_follow = [x.strip() for x in f.readlines()]

        #mylist = api.get_list()
        mylist = api.get_list(owner_screen_name='selenamarie', slug='womentofollow')
        print "%r" % mylist.id
        for person in people_to_follow:
            try:
                api.add_list_member(list_id=mylist.id, screen_name=person)
            except:
                # tweepy.error.TweepError: [{u'message': u"You've already requested to follow Pia_Gen", u'code': 160}]
                #error = tweepy.error.TweepError
                raise

    def print_opml(self, api, args):

        print "getting users"
        users = self.get_users(api, args)

        # truncate users to our stopafter point if specified
        print "truncating"
        if args.stop_after:
            users = users[1:args.stop_after]

        feeds = self.get_feeds(api, users, args)
        #feeds = get_feeds_from_entities(api, users, args)

        if args.output:
            sys.stdout = open(args.output, 'w')
        opml_start = """<?xml version="1.0" encoding="UTF-8"?>
        <opml version="1.1">
        <head>
        <title>%(title)s</title>
        </head>
        <body>
        <outline text="%(title)s" title="%(title)s">""" % {'title': args.title}

        opml_end = """</outline>
        </body>
        </opml>"""

        print opml_start

        opml_outline_feed = '<outline text="%(title)s" title="%(title)s" type="rss" version="RSS" htmlUrl="%(html_url)s" xmlUrl="%(xml_url)s" />'
        # Do this lookup in chunks of 100 because of twitter API limitations
        # Loop over URLS
        for f in feeds:
            if f:
                print opml_outline_feed % f

        print opml_end

    def __init__(self, args=None):
        pass

if __name__ == '__main__':

    conf_parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    conf_parser.add_argument("--config", dest="filename", help="Config File input", metavar="FILE", default=None)
    args, remaining_argv = conf_parser.parse_known_args()

    if args.filename:
        config = ConfigParser.SafeConfigParser()
        config.read([args.filename])
        defaults = dict(config.items("Defaults"))
    else:
        defaults = { "option":"default" }

    argparser = argparse.ArgumentParser(parents=[conf_parser])
    argparser.add_argument("--followers", help="fetch follower ids and urls", action="store_true", default=False)
    argparser.add_argument("--friends", help="fetch friend ids and urls", action="store_true", default=False)
    argparser.add_argument("--output", help="file to write output to", action="store", default=None)
    argparser.add_argument("--consumer_key", help="Consumer key (app dev)", action="store", default=None)
    argparser.add_argument("--consumer_secret", help="Consumer secret (app dev)", action="store", default=None)
    argparser.add_argument("--access_token", help="Twitter access token", action="store", default=None)
    argparser.add_argument("--access_token_secret", help="Twitter access token secret for user", action="store", default=None)
    argparser.add_argument("--chunks", help="chunks of users to query", action="store", default=100, type=int)
    argparser.add_argument("--stop_after", help="number of users to stop after", action="store", default=None, type=int)
    argparser.add_argument("--title", help="title for OPML file", action="store", default=None)
    argparser.add_argument("--to_follow", help="file of people to follow", action="store", default=None)
    argparser.add_argument("--to_unfollow", help="file of people to follow", action="store", default=None)
    argparser.add_argument("--all_followers", help="file of people to follow", action="store_true", default=False)
    argparser.add_argument("--update_list", help="file of people to follow", action="store", default=False)
    argparser.add_argument("--get_friends", help="fetch all friend nicknames", action="store_true", default=False)
    argparser.set_defaults(**defaults)
    args = argparser.parse_args(remaining_argv)

    opml = OPML(args)

    # Set a title for OPML if it hasn't already been set
    args = opml.pick_title(args)

    # Connect to twitter
    print "getting api connection"
    api = opml.connect_api(args)

    print "trying to print opml"
    # Print the OPML file
    #opml.print_opml(api, args)

    if args.get_friends is True:
        args.friends = True
        users =  opml.get_users(api, args)
        for user in users:
            print user
    elif args.to_follow is not None:
        opml.follow_women(api, args)
    elif args.all_followers is True:
        opml.find_women(api, args)
    elif args.update_list is not None:
        opml.update_list(api, args)
    elif args.to_unfollow is not None:
        opml.unfollow(api, args)
