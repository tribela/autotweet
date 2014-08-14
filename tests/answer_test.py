from pytest import fixture
from autotweet.database import (add_document, get_count, get_session,
                                get_best_answer)


@fixture
def fx_session():
    db_url = 'sqlite:///:memory:'

    return get_session(db_url)


def test_answers(fx_session):
    session = fx_session
    add_document(session, u'I like yummy cake', u'yummy cake')
    add_document(session, u'I like scary cake', u'scary cake')

    answer, ratio = get_best_answer(session, u'yummy pie')
    assert answer == u'yummy cake'
    answer, ratio = get_best_answer(session, u'scary pie')
    assert answer == u'scary cake'
    assert not get_best_answer(session, u'blabla')


def test_count(fx_session):
    session = fx_session
    assert get_count(session) == 0

    add_document(session, u'this is an apple.', u'I like apple.')
    assert get_count(session) == 1
    add_document(session, u'this is an apple.', u'I like apple.')
    assert get_count(session) == 1
