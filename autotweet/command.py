try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import argparse
import logging
import os
import waitress

from .answer import answer_daemon
from .app import app
from .database import add_document, get_session, init_db, recalc_idfs
from .learn import learning_daemon
from .twitter import authorize


def collector_command(args, config):
    try:
        token = config.get('auth', 'token')
    except configparser.NoOptionError:
        token = authorize().to_string()
        config.set('auth', 'token', token)

    db_url = config.get('database', 'db_url')
    token = config.get('auth', 'token')

    learning_daemon(token, db_url)


def answer_command(args, config):
    try:
        answerer_token = config.get('auth', 'answerer_token')
    except configparser.NoOptionError:
        answerer_token = authorize().to_string()
        config.set('auth', 'answerer_token', answerer_token)

    db_url = config.get('database', 'db_url')
    token = config.get('auth', 'answerer_token')
    try:
        threshold = config.getfloat('answer', 'threshold')
    except:
        threshold = None

    answer_daemon(token, db_url, threshold=threshold)


def server_command(args, config):
    db_url = config.get('database', 'db_url')
    app.config['DB_URI'] = db_url
    waitress.serve(app, host=args.host, port=args.port)


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


parser = argparse.ArgumentParser(prog='autotweet')
parser.add_argument('-c', '--config', help='config file')
parser.add_argument('-v', '--verbose', default=0, action='count',
                    help='Verbose output.')

subparsers = parser.add_subparsers(dest='command')

collector_parser = subparsers.add_parser(
    'collector',
    help='tweet collector for database')
collector_parser.set_defaults(function=collector_command)

answer_parser = subparsers.add_parser(
    'answer',
    help='Auto answer to mentions.')
answer_parser.set_defaults(function=answer_command)

server_parser = subparsers.add_parser(
    'server',
    help='server for simsim webservice')
server_parser.set_defaults(function=server_command)
server_parser.add_argument('-H', '--host',
                           default='0.0.0.0',
                           help='Host to listen. [default: %(default)s]')
server_parser.add_argument('-p', '--port',
                           type=int,
                           default=5000,
                           help='port number to listen. [default: %(default)s]')

add_parser = subparsers.add_parser(
    'add', help='manually add question and answer')
add_parser.set_defaults(function=add_command)
add_parser.add_argument('question', help='Question to add')
add_parser.add_argument('answer', help='Answer to add')

recalc_parser = subparsers.add_parser(
    'recalc', help='re-calculate idf for all grams')
recalc_parser.set_defaults(function=recalc_command)


config = configparser.ConfigParser()
config.add_section('auth')
config.add_section('database')


def set_logging_level(level):
    logging.basicConfig(format='%(levelname)s: %(message)s')

    if not level:
        logging.root.setLevel(logging.WARNING)
    elif level == 1:
        logging.root.setLevel(logging.INFO)
    else:
        logging.root.setLevel(logging.DEBUG)


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
        init_db(db_url)
    except configparser.NoOptionError:
        db_url = raw_input('db url: ').strip()
        config.set('database', 'db_url', db_url)
    with open(config_path, 'w') as fp:
        config.write(fp)

    args.function(args, config)


if __name__ == '__main__':
    main()
