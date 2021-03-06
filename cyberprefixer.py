#!/usr/bin/env python
# Copyright (c) 2013-2014 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import HTMLParser
import re
import tweepy
import urllib2
from secrets import *
from bs4 import BeautifulSoup
from topia.termextract import tag
from time import gmtime, strftime

tagger = tag.Tagger()
tagger.initialize()
hparser = HTMLParser.HTMLParser()

offensive = re.compile(r"\b(deaths?|dead(ly)?|die(s|d)?|hurts?|"
                       r"(sex|child)[ -]?(abuse|trafficking)|"
                       r"injur(e|i?es|ed|y)|kill(ing|ed|er|s)?s?|"
                       r"wound(ing|ed|s)?|fatal(ly|ity)?|shoo?t(s|ing|er)?s?|"
                       r"crash(es|ed|ing)?|attack(s|ers?|ing|ed)?|"
                       r"murder(s|er|ed|ing)?s?|hostages?|rap(e|es|ed|ing)|"
                       r"abduct(s|ed|ion)?s?|missing|"
                       r"assault(s|ed)?|pile-?ups?|massacre(s|d)?|"
                       r"assassinate(d|s)?|sla(y|in|yed|ys)|victims?|"
                       r"tortur(e|ed|ing|es)|execut(e|ion|ed)s?|"
                       r"gun(man|men|ned)|suicid(e|al|es)|bomb(s|ed)?|"
                       r"mass[- ]?graves?|bloodshed|state[- ]?of[- ]?emergency|"
                       r"al[- ]?Qaeda|blasts?|violen(t|ce))|lethal\W?\b",
                       flags=re.IGNORECASE)

def get():
    try:
        request = urllib2.Request(F_URL)
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        print e.reason
    else:
        html = BeautifulSoup(response.read())
        items = html.find_all('item')
        for item in items:
            headline = item.title.string
            h_split = headline.split()

            # We don't want to use incomplete headlines
            if "..." in headline:
                continue

            # Try to weed out all-caps headlines
            if count_caps(h_split) >= len(h_split) - 3:
                continue

            # Skip anything too offensive
            if not tact(headline):
                continue

            if process(headline):
                break

def process(headline):
    headline = hparser.unescape(headline).strip()
    tagged = tagger(headline)
    for i, word in enumerate(tagged):
        # Avoid having two "cybers" in a row
        if is_replaceable(word) and not is_replaceable(tagged[i-1]):
            headline = headline.replace(" " + word[0], " cyber" + word[0], 1)

    # Don't tweet anything that's too long or hasn't been replaced
    if "cyber" not in headline or len(headline) > 140:
        return False

    return tweet(headline)

def tweet(headline):
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = tweepy.API(auth)
    tweets = api.user_timeline(T_USERNAME, count=200)

    print "Attempting to tweet \"%s\"..." % headline

    # Check that we haven't tweeted this before
    for tweet in tweets:
        print "* Found tweet \"%s\"..." % tweet.text
        if headline == tweet.text:
            return False

    # Log tweet to file
    f = open("cyberprefixer.log", 'a')
    t = strftime("%d %b %Y %H:%M:%S", gmtime())
    f.write("\n" + t + " " + headline)
    f.close()

    # Post tweet
    api.update_status(headline)
    return True

def tact(headline):
    # Avoid producing particularly tactless tweets
    return re.search(offensive, headline) is None

def count_caps(headline):
    count = 0
    for word in headline:
        if word[0].isupper():
            count += 1
    return count

def is_replaceable(word):
    # Prefix any noun (singular or plural) that begins with a lowercase letter
    # and is longer than one character
    return (word[1] == 'NN' or word[1] == 'NNS') and \
           word[0][0].isalpha and \
           word[0][0].islower() and \
           len(word[0]) > 1

if __name__ == "__main__":
    get()
