import logging
import re
import tweepy
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, strip_tweet

MENTION_PATTERN = re.compile(r'(?<=\B@)\w+')


class MentionListener(tweepy.streaming.StreamListener):
    threshold = 0.3

    def __init__(self, api, atm, threshold=None):
        super(MentionListener, self).__init__()
        self.api = api
        self.atm = atm
        self.me = api.me()

        if threshold:
            self.threshold = threshold

    def on_status(self, status):
        if hasattr(status, 'retweeted_status'):
            return True

        user_name = status.user.screen_name
        mentions = set(MENTION_PATTERN.findall(status.text))
        mentions.discard(user_name)
        mentions.discard(self.me.screen_name)
        mentions = [user_name] + list(mentions)
        mentions = map(lambda x: '@' + x, mentions)

        question = strip_tweet(status.text)
        status_id = status.id

        (answer, ratio) = self.atm.get_best_answer(question)

        if (status.in_reply_to_user_id == self.me.id) or\
                (status.user.id != self.me.id and ratio >= self.threshold):
            logging.info(u'@{0.user.screen_name}: {0.text} -> {1}'.format(
                status, answer
                ))
            self.api.update_status(
                u'{0} {1}'.format(' '.join(mentions), answer),
                status_id)


def answer_daemon(token, atm, threshold=None):
    if not isinstance(token, tweepy.oauth.OAuthToken):
        token = tweepy.oauth.OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    listener = MentionListener(api, atm, threshold=threshold)

    stream = tweepy.Stream(auth, listener)
    stream.userstream()
