""":mod:`autotweet.answer` --- Answering module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module can auto answering to mentions to you or auto mentioning to others
tweet.

"""
import logging
import re
import time
import tweepy

from .database import NoAnswerError, get_best_answer, get_session
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, OAuthToken, strip_tweet

MENTION_PATTERN = re.compile(r'(?<=\B@)\w+')
DEFAULT_THRESHOLD = 0.3

logger = logging.getLogger('answer')


def get_friends(api):
    followings = set(user.screen_name for user in api.friends())
    followers = set(user.screen_name for user in api.followers())
    friends = followings | followers
    return friends


def get_mentions(status, friends):
    user_name = status.user.screen_name
    mentions = set(MENTION_PATTERN.findall(status.text))
    mentions.discard(user_name)
    mentions = mentions & friends
    mentions = [user_name] + list(mentions)
    mentions = map(lambda x: '@' + x, mentions)
    return mentions


class MentionListener(tweepy.streaming.StreamListener):
    threshold = DEFAULT_THRESHOLD
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
            self.friends = get_friends(self.api)
            self.friends_updated = time.time()
            return self.friends

    def on_status(self, status):
        if hasattr(status, 'retweeted_status') or status.user.id == self.me.id:
            return True

        mentions = get_mentions(status, self.get_friends())

        question = strip_tweet(status.text)
        status_id = status.id

        try:
            answer, ratio = get_best_answer(self.db_session, question)
        except NoAnswerError:
            return True

        if status.in_reply_to_user_id == self.me.id or ratio >= self.threshold:
            logger.info(u'@{0.user.screen_name}: {0.text} -> {1}'.format(
                status, answer
            ))
            try:
                self.api.update_status(
                    u'{0} {1}'.format(' '.join(mentions), answer),
                    status_id)
            except tweepy.error.TweepError as e:
                logger.error(u'Failed to update status: {0}'.format(
                    e.message
                ))


def polling_timeline(api, db_url, threshold=None):
    db_session = get_session(db_url)
    me = api.me()
    threshold = threshold or DEFAULT_THRESHOLD

    last_id = api.home_timeline(count=1)[0].id
    logger.debug('tracking from status id: {0}'.format(last_id))

    while 1:
        time.sleep(60)
        friends = get_friends(api)

        logger.debug('polling from status id: {0}'.format(last_id))
        if not threshold:
            statuses = api.mentions_timeline(since_id=last_id)
        else:
            home_timeline = api.home_timeline(since_id=last_id)
            mentions_timeline = api.mentions_timeline(since_id=last_id)
            home_ids = [status.id for status in home_timeline]

            statuses = home_timeline + [status for status in mentions_timeline
                                        if status.id not in home_ids]

        statuses = filter(lambda x: not hasattr(x, 'retweeted_status') and
                          x.user.id != me.id,
                          statuses)

        if statuses:
            statuses.reverse()
            last_id = statuses[-1].id
        else:
            continue

        for status in statuses:
            question = strip_tweet(status.text)
            mentions = get_mentions(status, friends)

            try:
                (answer, ratio) = get_best_answer(db_session, question)
            except NoAnswerError:
                pass

            if (status.in_reply_to_user_id == me.id) or\
               (status.user.id != me.id and ratio >= threshold):
                logger.info(u'@{0.user.screen_name}: {0.text} -> {1}'.format(
                    status, answer
                ))
                try:
                    api.update_status(
                        u'{0} {1}'.format(' '.join(mentions), answer),
                        status.id)
                except tweepy.error.TweepError as e:
                    logger.error(u'Failed to update status: {0}'.format(
                        e.message
                    ))


def answer_daemon(token, db_url, streaming=False, threshold=None):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    if streaming:
        listener = MentionListener(api, db_url, threshold=threshold)

        stream = tweepy.Stream(auth, listener)
        stream.userstream()
    else:
        polling_timeline(api, db_url, threshold)
