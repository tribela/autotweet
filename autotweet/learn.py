""":mod:`autotweet.learn` --- Learning your tweets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module learns your tweets and store it to database.

"""
import logging
import re
import sqlalchemy
import time
import tweepy
from .database import add_document, get_session
from .twitter import CONSUMER_KEY, CONSUMER_SECRET, OAuthToken, strip_tweet

MY_CLIENT_NAME = 'learn your tweet'
IGNORE_PATTERN = re.compile(r'(@\w+\s+)*@\w+\s{2,}|^[^@]')
logger = logging.getLogger('collector')


def check_ignore(status):
    if hasattr(status, 'retweeted_status'):
        return True
    if status.source == MY_CLIENT_NAME:
        return True
    if IGNORE_PATTERN.match(status.text):
        return True

    return False


class MyMentionListener(tweepy.streaming.StreamListener):

    def __init__(self, api, db_url):
        super(MyMentionListener, self).__init__()
        self.api = api
        self.db_url = db_url
        self.db_session = get_session(db_url)
        self.me = api.me()

    def on_status(self, status):
        if check_ignore(status):
            return True

        if status.user.id == self.me.id and status.in_reply_to_status_id:
            original_status = self.api.get_status(status.in_reply_to_status_id)

            question = strip_tweet(original_status.text)
            answer = strip_tweet(status.text, remove_url=False)

            if question and answer:
                try:
                    add_document(self.db_session, question, answer)
                except sqlalchemy.exc.OperationalError:
                    self.db_session = get_session(self.db_url)
                    add_document(self.db_session, question, answer)

        return True


def polling_timeline(api, db_url):
    db_session = get_session(db_url)
    me = api.me()
    last_id = me.status.id

    logger.debug('tracking from status id: {0}'.format(last_id))
    while 1:
        time.sleep(60)
        logger.debug('polling from status id: {0}'.format(last_id))
        statuses = me.timeline(since_id=last_id)
        if statuses:
            statuses.reverse()
            last_id = statuses[-1].id
        else:
            continue

        for status in statuses:
            if check_ignore(status):
                continue
            if not status.in_reply_to_status_id:
                continue

            original_status = api.get_status(status.in_reply_to_status_id)

            question = strip_tweet(original_status.text)
            answer = strip_tweet(status.text, remove_url=False)

            if question and answer:
                try:
                    add_document(db_session, question, answer)
                except sqlalchemy.exc.OperationalError:
                    db_session = get_session(db_url)
                    add_document(db_session, question, answer)


def import_timeline(token, db_url, count):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    db_session = get_session(db_url)
    me = api.me()

    statuses = me.timeline(count=count)
    statuses.reverse()

    for status in statuses:
        if check_ignore(status):
            continue
        if not status.in_reply_to_status_id:
            continue

        try:
            original_status = api.get_status(status.in_reply_to_status_id)
        except:
            continue

        question = strip_tweet(original_status.text)
        answer = strip_tweet(status.text, remove_url=False)

        if question and answer:
            add_document(db_session, question, answer)


def learning_daemon(token, db_url, streaming=False):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    if streaming:
        listener = MyMentionListener(api, db_url)

        stream = tweepy.Stream(auth, listener)
        stream.userstream()
    else:
        polling_timeline(api, db_url)
