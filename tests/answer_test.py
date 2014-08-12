import os
from pytest import fixture
from autotweet.database import (add_document, get_session, init_db,
                                get_best_answer)

@fixture
def fx_session(tmpdir):
    tmpdir = str(tmpdir)
    db_file = os.path.join(tmpdir, 'tmp.db')
    if os.path.exists(db_file):
        os.unlink(db_file)
    db_url = 'sqlite:///' + db_file

    init_db(db_url)
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
