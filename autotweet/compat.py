import sys

PY3 = sys.version_info >= (3, 0, 0)


def to_unicode(s):
    if PY3:
        if not isinstance(s, str):
            s = s.decode('utf-8')

    else:
        if isinstance(s, str):
            s = s.decode('utf-8')

    return s


if PY3:
    input = input
else:
    input = raw_input  # noqa
