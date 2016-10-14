""":mod:`autotweet.daemons` --- Learning, Answering your tweets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module learns your tweets and answering it automatically.

"""
from __future__ import unicode_literals
import logging
import re
import time
import tweepy

from .learning import NoAnswerError, DataCollection
from .twitter import (CONSUMER_KEY, CONSUMER_SECRET, OAuthToken, expand_url,
                      strip_tweet)


MY_CLIENT_NAME = 'learn your tweet'
IGNORE_PATTERN = re.compile(r'(@\w+\s+)*@\w+\s{2,}|^[^@]')
collector_logger = logging.getLogger('collector')

MENTION_PATTERN = re.compile(r'(?<=\B@)\w+')
DEFAULT_THRESHOLD = 0.3
answer_logger = logging.getLogger('answer')


def check_ignore(status):
    if hasattr(status, 'retweeted_status'):
        return True
    if status.source == MY_CLIENT_NAME:
        return True
    if IGNORE_PATTERN.match(status.text):
        return True

    return False


class CollectorMentionListener(tweepy.streaming.StreamListener):

    def __init__(self, api, db_url):
        super(CollectorMentionListener, self).__init__()
        self.api = api
        self.data_collection = DataCollection(db_url)
        self.me = api.me()

    def on_status(self, status):
        if check_ignore(status):
            return True

        if status.user.id == self.me.id and status.in_reply_to_status_id:
            original_status = self.api.get_status(status.in_reply_to_status_id)

            question = strip_tweet(original_status.text)
            answer = strip_tweet(expand_url(status.text), remove_url=False)

            if question and answer:
                self.data_collection.add_document(question, answer)

        return True


def collector_polling_timeline(api, db_url):
    data_collection = DataCollection(db_url)
    me = api.me()
    last_id = me.status.id

    collector_logger.debug('tracking from status id: {0}'.format(last_id))
    while 1:
        time.sleep(60)
        collector_logger.debug('polling from status id: {0}'.format(last_id))
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
                data_collection.add_document(question, answer)


def import_timeline(token, db_url, count):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    data_collection = DataCollection(db_url)
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
            data_collection.add_document(question, answer)


def learning_daemon(token, db_url, streaming=False):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    if streaming:
        listener = CollectorMentionListener(api, db_url)

        stream = tweepy.Stream(auth, listener)
        stream.userstream()
    else:
        collector_polling_timeline(api, db_url)


# Moved from answer


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


class AnswerMentionListener(tweepy.streaming.StreamListener):
    threshold = DEFAULT_THRESHOLD
    friends_timeout = 60
    friends_updated = None

    def __init__(self, api, db_url, threshold=None):
        super(AnswerMentionListener, self).__init__()
        self.api = api
        self.data_collection = DataCollection(db_url)
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
            answer, ratio = self.data_collection.get_best_answer(question)
        except NoAnswerError:
            return True

        if status.in_reply_to_user_id == self.me.id or ratio >= self.threshold:
            answer_logger.info('@{0.user.screen_name}: {0.text} -> {1}'.format(
                status, answer
            ))
            try:
                self.api.update_status(
                    status='{0} {1}'.format(' '.join(mentions), answer),
                    in_reply_to_status_id=status_id)
            except tweepy.error.TweepError as e:
                answer_logger.error('Failed to update status: {0}'.format(
                    e.message
                ))


def answer_polling_timeline(api, db_url, threshold=None):
    data_collection = DataCollection(db_url)
    me = api.me()
    threshold = threshold or DEFAULT_THRESHOLD

    last_id = api.home_timeline(count=1)[0].id
    answer_logger.debug('tracking from status id: {0}'.format(last_id))

    while 1:
        time.sleep(60)
        friends = get_friends(api)

        answer_logger.debug('polling from status id: {0}'.format(last_id))
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
                (answer, ratio) = data_collection.get_best_answer(question)
            except NoAnswerError:
                pass

            if (status.in_reply_to_user_id == me.id) or \
                    (status.user.id != me.id and ratio >= threshold):
                answer_logger.info(
                    '@{0.user.screen_name}: {0.text} -> {1}'.format(
                        status, answer
                    ))
                try:
                    api.update_status(
                        status='{0} {1}'.format(' '.join(mentions), answer),
                        in_reply_to_status_id=status.id)
                except tweepy.error.TweepError as e:
                    answer_logger.error('Failed to update status: {0}'.format(
                        e.message
                    ))


def answer_daemon(token, db_url, streaming=False, threshold=None):
    if not isinstance(token, OAuthToken):
        token = OAuthToken.from_string(token)

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    if streaming:
        listener = AnswerMentionListener(api, db_url, threshold=threshold)

        stream = tweepy.Stream(auth, listener)
        stream.userstream()
    else:
        answer_polling_timeline(api, db_url, threshold)
