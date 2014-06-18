import re
import tweepy
import webbrowser
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


CONSUMER_KEY = '62yWrV2RhpGgWOKlqvJPNQ'
CONSUMER_SECRET = 'Je6NLI7AN3c1BJP9kHaq1p8GBkMyKs5GhX954dWJ6I'

url_pattern = re.compile(r'https?://[^\s]+')
mention_pattern = re.compile(r'@\w+')
html_parser = HTMLParser()


def authorize():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    url = auth.get_authorization_url()
    print('Open this url on your webbrowser: {0}'.format(url))
    webbrowser.open(url)
    pin = raw_input('Input verification number here: ').strip()

    token = auth.get_access_token(verifier=pin)

    return token


def strip_tweet(text, remove_url=True):
    if remove_url:
        text = url_pattern.sub('', text)
    text = mention_pattern.sub('', text)
    text = html_parser.unescape(text)
    text = text.strip()
    return text
