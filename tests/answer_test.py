from autotweet.database import AutoAnswer


def test_answers():
    aa = AutoAnswer('sqlite:///:memory:')
    aa.add_document(u'I like yummy cake', u'yummy cake')
    aa.add_document(u'I like scary cake', u'scary cake')

    answer, ratio = aa.get_best_answer(u'yummy pie')
    assert answer == u'yummy cake'
    answer, ratio = aa.get_best_answer(u'scary pie')
    assert answer == u'scary cake'
    assert not aa.get_best_answer(u'blabla')
