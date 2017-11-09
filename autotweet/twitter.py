""":mod:`autotweet.twitter` --- Twitter utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Twitter API key and some useful methods.

"""
from __future__ import unicode_literals
import cgi
import re
import tweepy
import webbrowser
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser
try:
    from urllib import urlencode
    from urllib2 import urlopen
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import urlopen

from .compat import input


__all__ = ('CONSUMER_KEY', 'CONSUMER_SECRET', 'authorize', 'strip_tweet')


#: Consumer key for autoweet.
CONSUMER_KEY = '62yWrV2RhpGgWOKlqvJPNQ'
#: Consumer secret key for autotweet.
CONSUMER_SECRET = 'Je6NLI7AN3c1BJP9kHaq1p8GBkMyKs5GhX954dWJ6I'

url_pattern = re.compile(r'https?://[^\s]+')
mention_pattern = re.compile(r'@\w+')
html_parser = HTMLParser()


class OAuthToken(object):
    key = None
    secret = None

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def to_string(self):
        return urlencode({
            'oauth_token': self.key,
            'oauth_token_secret': self.secret,
        })

    @staticmethod
    def from_string(string):
        params = cgi.parse_qs(string, keep_blank_values=False)
        key = params['oauth_token'][0]
        secret = params['oauth_token_secret'][0]
        return OAuthToken(key, secret)


def authorize():
    """Authorize to twitter.

    Use PIN authentification.

    :returns: Token for authentificate with Twitter.
    :rtype: :class:`autotweet.twitter.OAuthToken`

    """
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    url = auth.get_authorization_url()
    print('Open this url on your webbrowser: {0}'.format(url))
    webbrowser.open(url)
    pin = input('Input verification number here: ').strip()

    token_key, token_secret = auth.get_access_token(verifier=pin)

    return OAuthToken(token_key, token_secret)


def get_api(token):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    return api


def expand_url(status):
    """Expand url on statuses.

    :param status: A tweepy status to expand urls.
    :type status: :class:`tweepy.models.Status`
    :returns: A string with expanded urls.
    :rtype: :class:`str`
    """

    try:
        txt = get_full_text(status)
        for url in status.entities['urls']:
            txt = txt.replace(url['url'], url['expanded_url'])
    except:
        # Manually replace
        txt = status
        tco_pattern = re.compile(r'https://t.co/\S+')
        urls = tco_pattern.findall(txt)
        for url in urls:
            with urlopen(url) as resp:
                expanded_url = resp.url
            txt = txt.replace(url, expanded_url)

    return txt


def get_full_text(status):
    if hasattr(status, 'extended_tweet'):
        return status.extended_tweet['full_text']
    elif hasattr(status, 'full_text'):
        return status.full_text

    return status.text


def strip_tweet(text, remove_url=True):
    """Strip tweet message.

    This method removes mentions strings and urls(optional).

    :param text: tweet message
    :type text: :class:`str`

    :param remove_url: Remove urls. default :const:`True`.
    :type remove_url: :class:`boolean`

    :returns: Striped tweet message
    :rtype: :class:`str`

    """
    if remove_url:
        text = url_pattern.sub('', text)
    else:
        text = expand_url(text)
    text = mention_pattern.sub('', text)
    text = html_parser.unescape(text)
    text = text.strip()
    return text
