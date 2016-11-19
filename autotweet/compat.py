import sys


def to_unicode(s):
    if sys.version_info >= (3, 0, 0):
        if not isinstance(s, str):
            s = s.decode('utf-8')

    else:
        if isinstance(s, str):
            s = s.decode('utf-8')

    return s
