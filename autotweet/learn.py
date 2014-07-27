import tweepy
from .database import add_document, get_session
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, strip_tweet


class MyMentionListener(tweepy.streaming.StreamListener):

    def __init__(self, api, db_url):
        super(MyMentionListener, self).__init__()
        self.api = api
        self.db_session = get_session(db_url)
        self.me = api.me()

    def on_status(self, status):
        if hasattr(status, 'retweeted_status'):
            return True

        if status.user.id == self.me.id and status.in_reply_to_status_id:
            original_status = self.api.get_status(status.in_reply_to_status_id)

            question = strip_tweet(original_status.text)
            answer = strip_tweet(status.text, remove_url=False)

            if question and answer:
                add_document(self.db_session, question, answer)

        return True


def learning_daemon(token, db_url):
    if not isinstance(token, tweepy.oauth.OAuthToken):
        token = tweepy.oauth.OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    listener = MyMentionListener(api, db_url)

    stream = tweepy.Stream(auth, listener)
    stream.userstream()
