from __future__ import unicode_literals

import logging

root_logger = logging.getLogger('autotweet')

logging.basicConfig(
    format='%(asctime)s {%(module)s:%(levelname)s}: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


def set_level(level):
    root_logger.setLevel(level)


get_logger = root_logger.getChild
