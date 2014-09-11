try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import argparse
import logging
import os
import tweepy

from .answer import answer_daemon
from .database import (add_document, get_session, recalc_idfs,
                       recreate_grams)
from .learn import learning_daemon
from .twitter import authorize, CONSUMER_KEY, CONSUMER_SECRET


logger = logging.getLogger('command')


def collector_command(args, config):
    try:
        token = config.get('auth', 'token')
    except configparser.NoOptionError:
        token = authorize().to_string()
        config.set('auth', 'token', token)
        write_config(args, config)

    db_url = config.get('database', 'db_url')
    token = config.get('auth', 'token')

    learning_daemon(token, db_url, args.stream)


def answer_command(args, config):
    try:
        answerer_token = config.get('auth', 'answerer_token')
    except configparser.NoOptionError:
        answerer_token = authorize().to_string()
        config.set('auth', 'answerer_token', answerer_token)
        write_config(args, config)

    db_url = config.get('database', 'db_url')
    token = config.get('auth', 'answerer_token')
    try:
        threshold = config.getfloat('answer', 'threshold')
    except:
        threshold = None

    answer_daemon(token, db_url, args.stream, threshold=threshold)


def after_death_command(args, config):
    try:
        my_token = config.get('auth', 'token')
    except configparser.NoOptionError:
        my_token = authorize().to_string()
        config.set('auth', 'token', my_token)
        write_config(args, config)

    token = tweepy.oauth.OAuthToken.from_string(my_token)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(token.key, token.secret)
    api = tweepy.API(auth)

    try:
        auto_tweets = config.items('tweet after death')
    except configparser.NoOptionError:
        auto_tweets = []

    for key, item in auto_tweets:
        try:
            api.update_status(item)
            logger.info(u'Tweet item: {0}'.format(item))
        except tweepy.error.TweepError as e:
            logger.error(u'Failed to update status: {0}'.format(e.message))

    db_url = config.get('database', 'db_url')

    try:
        threshold = config.getfloat('answer', 'threshold')
    except:
        threshold = None

    answer_daemon(my_token, db_url, threshold=threshold)


def add_command(args, config):
    db_url = config.get('database', 'db_url')
    question = args.question.decode('utf-8')
    answer = args.answer.decode('utf-8')

    session = get_session(db_url)

    add_document(session, question, answer)


def recalc_command(args, config):
    db_url = config.get('database', 'db_url')
    session = get_session(db_url)
    recalc_idfs(session)


def recreate_command(args, config):
    db_url = config.get('database', 'db_url')
    session = get_session(db_url)
    recreate_grams(session)


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

add_parser = subparsers.add_parser(
    'add', help='manually add question and answer')
add_parser.set_defaults(function=add_command)
add_parser.add_argument('question', help='Question to add')
add_parser.add_argument('answer', help='Answer to add')

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


def write_config(args, config):
    config_path = args.config or os.path.join(os.getenv('HOME'), '.autotweetrc')
    with open(config_path, 'w') as fp:
        config.write(fp)


def main():
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    config_path = args.config or os.path.join(os.getenv('HOME'), '.autotweetrc')
    config.read(config_path)

    set_logging_level(args.verbose)

    try:
        db_url = config.get('database', 'db_url')
    except configparser.NoOptionError:
        db_url = raw_input('db url: ').strip()
        config.set('database', 'db_url', db_url)

    write_config(args, config)

    args.function(args, config)


if __name__ == '__main__':
    main()
