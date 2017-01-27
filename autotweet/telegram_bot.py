# coding: utf-8
""":mod:`autotweet.command` --- CLI interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides abillities to connect to telegram.

"""
from __future__ import unicode_literals

import re

from telegram.ext import (
    BaseFilter, CommandHandler, Filters, MessageHandler, Updater)

from .learning import DataCollection, NoAnswerError
from .logger_factory import get_logger
from .twitter import strip_tweet


class ReplyFilter(BaseFilter):
    def filter(self, message):
        return bool(message.reply_to_message)


Filters.reply = ReplyFilter()

logger = get_logger(__name__)


class TelegramBot(object):
    def __init__(self, db_uri, token, threshold, learning=True, answering=True):
        self._make_updater(token)

        self.threshold = threshold
        self.data_collection = DataCollection(db_uri)

        self._init_handlers()
        if learning:
            self.enable_learning()
        if answering:
            self.enable_answering()

    def run(self):
        logger.info('Starting with {} documents.'.format(
            self.data_collection.get_count()))
        self.me = self.updater.bot.get_me()
        self.updater.start_polling()
        self.updater.idle()

    def learning_handler(self, bot, update):
        question = strip_tweet(update.message.reply_to_message.text)
        answer = strip_tweet(update.message.text, remove_url=False)
        self.data_collection.add_document(question, answer)

    def answering_handler(self, bot, update):
        question = strip_tweet(update.message.text)
        try:
            answer, ratio = self.data_collection.get_best_answer(question)
            if (ratio > self.threshold or
                    self._is_necessary_to_reply(bot, update)):
                logger.info('{} -> {}'.format(question, answer))
                update.message.reply_text(answer)
        except NoAnswerError:
            logger.debug('No answer to {}'.format(update.message.text))
            if self._is_necessary_to_reply(bot, update):
                update.message.reply_text(r'¯\_(ツ)_/¯')

    def leave_handler(self, bot, update):
        logger.info('Leave from chat {}'.format(update.message.chat_id))
        bot.leave_chat(update.message.chat_id)

    def enable_learning(self):
        logger.debug('Enabling learning handler.')
        self.dispatcher.add_handler(
            MessageHandler(Filters.reply, self.learning_handler))

    def enable_answering(self):
        logger.debug('Enabling answer handler.')
        self.dispatcher.add_handler(
            MessageHandler(Filters.text, self.answering_handler))

    def _make_updater(self, token):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

    def _init_handlers(self):
        self.dispatcher.add_handler(CommandHandler('leave', self.leave_handler))

    def _is_necessary_to_reply(self, bot, update):
        message = update.message

        if message.chat.type == 'private':
            logger.debug('{} type private'.format(message.text))
            return True

        matched = re.search(r'@{}\b'.format(self.me.username), message.text)
        result = bool(matched)
        if result:
            logger.debug('{} mentioned me.'.format(message.text))
            return True

        return False


def start_bot(token, db_uri, threshold, learning=True, answering=True):
    bot = TelegramBot(db_uri, token, threshold, learning, answering)
    bot.run()
