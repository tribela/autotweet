""":mod:`autotweet.command` --- CLI interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides command line interface.

"""
from __future__ import unicode_literals
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import argparse
import logging
import os
import tweepy

from .daemons import answer_daemon, import_timeline, learning_daemon
from .learning import DataCollection
from .twitter import authorize, CONSUMER_KEY, CONSUMER_SECRET, OAuthToken


logger = logging.getLogger('command')


def get_token_string(config_path, key_name):
    try:
        token_string = config.get('auth', key_name)
    except configparser.NoOptionError:
        token = authorize()
        token_string = token.to_string()
        config.set('auth', key_name, token_string)
        write_config(config_path, config)

    return token_string


def collector_command(args, config):
    token_string = get_token_string(args.config, 'token')
    db_url = config.get('database', 'db_url')

    learning_daemon(token_string, db_url, args.stream)


def answer_command(args, config):
    token_string = get_token_string(args.config, 'answerer_token')
    db_url = config.get('database', 'db_url')
    try:
        threshold = config.getfloat('answer', 'threshold')
    except:
        threshold = None

    answer_daemon(token_string, db_url, args.stream, threshold=threshold)


def after_death_command(args, config):
    token_string = get_token_string(args.config, 'token')

    token_key, token_secret = OAuthToken.from_string(token_string)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token_key, token_secret)
    api = tweepy.API(auth)

    try:
        auto_tweets = config.items('tweet after death')
    except configparser.NoOptionError:
        auto_tweets = []

    for key, item in auto_tweets:
        try:
            api.update_status(status=item)
            logger.info('Tweet item: {0}'.format(item))
        except tweepy.error.TweepError as e:
            logger.error('Failed to update status: {0}'.format(e.message))

    db_url = config.get('database', 'db_url')

    try:
        threshold = config.getfloat('answer', 'threshold')
    except:
        threshold = None

    answer_daemon(token_string, db_url, threshold=threshold)


def add_command(args, config):
    db_url = config.get('database', 'db_url')
    question = args.question.decode('utf-8')
    answer = args.answer.decode('utf-8')

    data_collection = DataCollection(db_url)

    data_collection.add_document(question, answer)


def get_command(args, config):
    db_url = config.get('database', 'db_url')
    question = args.question.decode('utf-8')

    data_collection = DataCollection(db_url)
    answer, ratio = data_collection.get_best_answer(question)
    print('{} (ratio: {})'.format(answer, ratio))


def import_command(args, config):
    token_string = get_token_string(args.config, 'token')
    db_url = config.get('database', 'db_url')

    import_timeline(token_string, db_url, args.count)


def recalc_command(args, config):
    db_url = config.get('database', 'db_url')
    data_collection = DataCollection(db_url)
    data_collection.recalc_idfs()


def recreate_command(args, config):
    db_url = config.get('database', 'db_url')
    data_collection = DataCollection(db_url)
    data_collection.recreate_grams()


parser = argparse.ArgumentParser(prog='autotweet')
parser.add_argument('-c', '--config', help='config file')
parser.add_argument('-v', '--verbose', default=0, action='count',
                    help='Verbose output.')

subparsers = parser.add_subparsers(dest='command')

collector_parser = subparsers.add_parser(
    'collector',
    help='tweet collector for database')
collector_parser.set_defaults(function=collector_command)
collector_parser.add_argument('-s', '--stream',
                              help='use streaming to collect tweet',
                              action='store_true', default=False)

answer_parser = subparsers.add_parser(
    'answer',
    help='Auto answer to mentions.')
answer_parser.set_defaults(function=answer_command)
answer_parser.add_argument('-s', '--stream',
                           help='use streaming to collect tweet',
                           action='store_true', default=False)

after_death_parser = subparsers.add_parser(
    'after_death',
    help='tweet after death.'
    ' When you run this command, you has be replaced by autotweet.')
after_death_parser.set_defaults(function=after_death_command)
after_death_parser.add_argument('-s', '--stream',
                                help='use streaming to collect tweet',
                                action='store_true', default=False)

add_parser = subparsers.add_parser(
    'add', help='manually add question and answer')
add_parser.set_defaults(function=add_command)
add_parser.add_argument('question', help='Question to add')
add_parser.add_argument('answer', help='Answer to add')

get_parser = subparsers.add_parser(
     'get', help='Get best answer from CLI')
get_parser.set_defaults(function=get_command)
get_parser.add_argument('question', help='Question to answer')

import_parser = subparsers.add_parser(
    'import', help='Import from your last statuses')
import_parser.set_defaults(function=import_command)
import_parser.add_argument('-c', '--count',
                           help='Count for import last statuses',
                           type=int, default=1000)

recalc_parser = subparsers.add_parser(
    'recalc', help='re-calculate idf for all grams')
recalc_parser.set_defaults(function=recalc_command)

recreate_parser = subparsers.add_parser(
    'recreate', help='re-create grams for all documents')
recreate_parser.set_defaults(function=recreate_command)


config = configparser.ConfigParser()
config.add_section('auth')
config.add_section('database')
config.add_section('tweet after death')


def set_logging_level(level):

    if not level:
        log_level = logging.WARNING
    elif level == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    logging.basicConfig(
        format='%(asctime)s {%(module)s:%(levelname)s}: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger('database').setLevel(log_level)
    logging.getLogger('answer').setLevel(log_level)
    logging.getLogger('command').setLevel(log_level)
    logging.getLogger('collector').setLevel(log_level)


def write_config(config_path, config):
    with open(config_path, 'w') as fp:
        config.write(fp)


def main():
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    args.config = args.config or os.path.join(os.getenv('HOME'), '.autotweetrc')
    config.read(args.config)

    set_logging_level(args.verbose)

    try:
        db_url = config.get('database', 'db_url')
    except configparser.NoOptionError:
        db_url = raw_input('db url: ').strip()
        config.set('database', 'db_url', db_url)

    write_config(args.config, config)

    args.function(args, config)


if __name__ == '__main__':
    main()
