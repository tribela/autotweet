from autotweet.database import add_document, get_best_answer, init_db


def test_answers():
    session = init_db('sqlite:///:memory:')
    add_document(session, u'I like yummy cake', u'yummy cake')
    add_document(session, u'I like scary cake', u'scary cake')

    assert get_best_answer(session, u'yummy pie') == u'yummy cake'
    assert get_best_answer(session, u'scary pie') == u'scary cake'
    assert not get_best_answer(session, u'blabla')
