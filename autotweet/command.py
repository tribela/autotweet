try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import argparse
import os

from .database import init_db
from .learn import authorize, learning_daemon


parser = argparse.ArgumentParser(prog='autotweet')
parser.add_argument('-c', '--config', help='config file')

config = configparser.ConfigParser()
config.add_section('auth')
config.add_section('database')


def main():
    args = parser.parse_args()
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

    session = init_db(db_url)
    learning_daemon(token, session)

if __name__ == '__main__':
    main()
