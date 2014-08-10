import logging
import re
import time
import tweepy

from .database import get_best_answer, get_session
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, strip_tweet

MENTION_PATTERN = re.compile(r'(?<=\B@)\w+')

logger = logging.getLogger('answer')


class MentionListener(tweepy.streaming.StreamListener):
    threshold = 0.3
    friends_timeout = 60
    friends_updated = None

    def __init__(self, api, db_url, threshold=None):
        super(MentionListener, self).__init__()
        self.api = api
        self.db_session = get_session(db_url)
        self.me = api.me()

        if threshold:
            self.threshold = threshold

    def get_friends(self):
        if self.friends_updated is None or \
           time.time() - self.friends_updated > self.friends_timeout:
            followings = set(user.screen_name for user in self.api.friends())
            followers = set(user.screen_name for user in self.api.followers())
            self.friends = followings | followers
            self.friends_updated = time.time()
        return self.friends

    def on_status(self, status):
        if hasattr(status, 'retweeted_status'):
            return True

        user_name = status.user.screen_name
        mentions = set(MENTION_PATTERN.findall(status.text))
        mentions.discard(user_name)
        mentions = mentions & self.get_friends()
        mentions = [user_name] + list(mentions)
        mentions = map(lambda x: '@' + x, mentions)

        question = strip_tweet(status.text)
        status_id = status.id

        result = get_best_answer(self.db_session, question)
        if not result:
            return True
        (answer, ratio) = result

        if (status.in_reply_to_user_id == self.me.id) or\
                (status.user.id != self.me.id and ratio >= self.threshold):
            logger.info(u'@{0.user.screen_name}: {0.text} -> {1}'.format(
                status, answer
                ))
            self.api.update_status(
                u'{0} {1}'.format(' '.join(mentions), answer),
                status_id)


def answer_daemon(token, db_url, threshold=None):
    if not isinstance(token, tweepy.oauth.OAuthToken):
        token = tweepy.oauth.OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    listener = MentionListener(api, db_url, threshold=threshold)

    stream = tweepy.Stream(auth, listener)
    stream.userstream()
