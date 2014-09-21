""":mod:`autotweet.twitter` --- Twitter utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains Twitter API key and some useful methods.

"""
import re
import tweepy
import webbrowser
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


__all__ = ('CONSUMER_KEY', 'CONSUMER_SECRET', 'authorize', 'strip_tweet')


#: Consumer key for autoweet.
CONSUMER_KEY = '62yWrV2RhpGgWOKlqvJPNQ'
#: Consumer secret key for autotweet.
CONSUMER_SECRET = 'Je6NLI7AN3c1BJP9kHaq1p8GBkMyKs5GhX954dWJ6I'

url_pattern = re.compile(r'https?://[^\s]+')
mention_pattern = re.compile(r'@\w+')
html_parser = HTMLParser()


def authorize():
    """Authorize to twitter.

    Use PIN authentification.

    :returns: Token for authentificate with Twitter.
    :rtype: :class:`autotweet.oauth.OAuthToken`

    """
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    url = auth.get_authorization_url()
    print('Open this url on your webbrowser: {0}'.format(url))
    webbrowser.open(url)
    pin = raw_input('Input verification number here: ').strip()

    token = auth.get_access_token(verifier=pin)

    return token


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
    text = mention_pattern.sub('', text)
    text = html_parser.unescape(text)
    text = text.strip()
    return text
