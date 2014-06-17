import tweepy
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, strip_tweet


class MentionListener(tweepy.streaming.StreamListener):

    def __init__(self, api, atm):
        super(MentionListener, self).__init__()
        self.api = api
        self.atm = atm
        self.me = api.me()

    def on_status(self, status):
        if hasattr(status, 'retweeted_status'):
            return True

        if status.in_reply_to_user_id == self.me.id:
            question = strip_tweet(status.text)
            user_name = status.user.screen_name
            status_id = status.id

            (answer, ratio) = self.atm.get_best_answer(question)

            self.api.update_status(
                u'@{0} {1}'.format(user_name, answer),
                status_id)


def answer_daemon(token, atm):
    if not isinstance(token, tweepy.oauth.OAuthToken):
        token = tweepy.oauth.OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    listener = MentionListener(api, atm)

    stream = tweepy.Stream(auth, listener)
    stream.userstream()
