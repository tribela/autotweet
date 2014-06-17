try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import argparse
import os
import waitress

from .database import AutoAnswer
from .learn import authorize, learning_daemon
from .app import app, spawn_worker


def collector_command(args, config):
    db_url = config.get('database', 'db_url')
    token = config.get('auth', 'token')

    atm = AutoAnswer(db_url)
    learning_daemon(token, atm)


def server_command(args, config):
    db_url = config.get('database', 'db_url')
    atm = AutoAnswer(db_url)
    app.config.update(atm=atm)
    spawn_worker()
    waitress.serve(app, host='0.0.0.0', port=8080)


parser = argparse.ArgumentParser(prog='autotweet')
parser.add_argument('-c', '--config', help='config file')

subparsers = parser.add_subparsers(dest='command')

collector_parser = subparsers.add_parser(
    'collector',
    help='tweet collector for database')
collector_parser.set_defaults(function=collector_command)

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


config = configparser.ConfigParser()
config.add_section('auth')
config.add_section('database')


def main():
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    config_path = args.config or os.path.join(os.getenv('HOME'), '.autotweetrc')
    config.read(config_path)

    try:
        db_url = config.get('database', 'db_url')
    except configparser.NoOptionError:
        db_url = raw_input('db url: ').strip()
        config.set('database', 'db_url', db_url)

    try:
        token = config.get('auth', 'token')
    except configparser.NoOptionError:
        token = authorize().to_string()
        config.set('auth', 'token', token.to_string())

    with open(config_path, 'w') as fp:
        config.write(fp)

    args.function(args, config)


if __name__ == '__main__':
    main()
