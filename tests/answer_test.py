from pytest import fixture, raises
from autotweet.learning import DataCollection, NoAnswerError


@fixture
def fx_data_collection():
    db_url = 'sqlite:///:memory:'
    return DataCollection(db_url)


def test_answers(fx_data_collection):
    dc = fx_data_collection
    dc.add_document(u'I like yummy cake', u'yummy cake')
    dc.add_document(u'I like scary cake', u'scary cake')

    answer, ratio = dc.get_best_answer(u'yummy pie')
    assert answer == u'yummy cake'
    answer, ratio = dc.get_best_answer(u'scary pie')
    assert answer == u'scary cake'
    with raises(NoAnswerError):
        dc.get_best_answer(u'blabla')


def test_count(fx_data_collection):
    dc = fx_data_collection
    assert dc.get_count() == 0

    dc.add_document(u'this is an apple.', u'I like apple.')
    assert dc.get_count() == 1
    dc.add_document(u'this is an apple.', u'I like apple.')
    assert dc.get_count() == 1


def test_short_question(fx_data_collection):
    dc = fx_data_collection
    assert dc.get_count() == 0

    dc.add_document(u'c', u'cake')
    dc.add_document(u'l', u'lie')

    answer, ratio = dc.get_best_answer(u'c')
    assert answer == u'cake'

    answer, ratio = dc.get_best_answer(u'l')
    assert answer == u'lie'
