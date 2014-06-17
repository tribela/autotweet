import webbrowser
import time
import tweepy
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, strip_tweet


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
            answer = strip_tweet(status.text, remove_url=False)

            if question and answer:
                atm.add_document(question, answer)

        return True


def learning_daemon(token, atm):
    if not isinstance(token, tweepy.oauth.OAuthToken):
        token = tweepy.oauth.OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    listener = MyMentionListener(api, atm)

    stream = tweepy.Stream(auth, listener)
    stream.userstream()
