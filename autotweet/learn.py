import webbrowser
import re
import time
import tweepy


CONSUMER_KEY = '62yWrV2RhpGgWOKlqvJPNQ'
CONSUMER_SECRET = 'Je6NLI7AN3c1BJP9kHaq1p8GBkMyKs5GhX954dWJ6I'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

url_pattern = re.compile(r'https?://[^\s]+')
mention_pattern = re.compile(r'@\w+')


class MyMentionListener(tweepy.streaming.StreamListener):

    def __init__(self, api, atm):
        super(MyMentionListener, self).__init__()
        self.api = api
        self.atm = atm
        self.me = api.me()

    def on_status(self, status):
        if hasattr(status, 'retweeted_status'):
            return True

        if status.user.id == self.me.id and status.in_reply_to_status_id:
            original_status = self.api.get_status(status.in_reply_to_status_id)

            question = strip_tweet(original_status.text)
            answer = mention_pattern.sub('', status.text)

            if question and answer:
                atm.add_document(question, answer)

        return True


def authorize():
    url = auth.get_authorization_url()
    print('Open this url on your webbrowser: {0}'.format(url))
    webbrowser.open(url)
    pin = raw_input('Input verification number here: ').strip()

    token = auth.get_access_token(verifier=pin)

    return token


def strip_tweet(text):
    text = url_pattern.sub('', text)
    text = mention_pattern.sub('', text)
    text = text.strip()
    return text


def learning_daemon(token, atm):
    if not isinstance(token, tweepy.oauth.OAuthToken):
        token = tweepy.oauth.OAuthToken.from_string(token)

    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    listener = MyMentionListener(api, atm)

    stream = tweepy.Stream(auth, listener)
    stream.userstream()
