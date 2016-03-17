import logging
import math
import random

from .database import GRAM_LENGTH, Document, Gram


__all__ = ('NoAnswerError', 'get_count', 'add_document', 'get_best_answer',
           'recreate_grams', 'recalc_idfs')

logger = logging.getLogger('learning')


def add_document(session, question, answer):
    """Add question answer set to DB.

    :param session: DB session
    :type session: :class:`sqlalchemt.orm.Session`

    :param question: A question to an answer
    :type question: :class:`str`

    :param answer: An answer to a question
    :type answer: :class:`str`

    """
    question = question.strip()
    answer = answer.strip()

    if session.query(Document) \
            .filter_by(text=question, answer=answer).count():
        logger.info(u'Already here: {0} -> {1}'.format(question, answer))
        return
    logger.info(u'add document: {0} -> {1}'.format(question, answer))

    grams = _get_grams(session, question, make=True)

    doc = Document(question, answer)
    doc.grams = list(grams)
    recalc_idfs(session, grams)

    session.add(doc)
    session.commit()


def get_best_answer(session, query):
    """Get best answer to a question.

    :param session: DB session
    :type session: :class:`sqlalchemt.orm.Session`

    :param query: A question to get an answer
    :type query: :class:`str`

    :returns: An answer to a question
    :rtype: :class:`str`

    :raises: :class:`NoAnswerError` when can not found answer to a question

    """
    if isinstance(query, buffer):
        query = str(query)
    if not isinstance(query, unicode):
        query = query.decode('utf-8')

    grams = _get_grams(session, query)
    if not grams:
        raise NoAnswerError('Can not found answer')

    documents = set([doc for gram in grams for doc in gram.documents])

    recalc_idfs(session, grams)

    idfs = dict((gram.gram, gram.idf) for gram in grams)

    docs = dict(
        (doc.answer, _cosine_measure(idfs, _get_tf_idfs(session, doc)))
        for doc in documents)
    docs = dict((key, val) for (key, val) in docs.items() if val)

    session.commit()

    try:
        max_ratio = max(docs.values())
        answers = [answer for answer in docs.keys()
                   if docs.get(answer) == max_ratio]

        answer = random.choice(answers)
        logger.debug(u'{0} -> {1} ({2})'.format(query, answer, max_ratio))
        return (answer, max_ratio)
    except ValueError:
        raise NoAnswerError('Can not found answer')


def recreate_grams(session):
    """Re-create grams for database.

    In normal situations, you never need to call this method.
    But after migrate DB, this method is useful.

    :param session: DB session
    :type session: :class:`sqlalchemt.orm.Session`

    """

    for document in session.query(Document).all():
        grams = _get_grams(session, document.text, make=True)
        document.grams = list(grams)

    broken_links = session.query(Gram) \
        .filter(~Gram.documents.any()).all()
    for gram in broken_links:
        session.delete(gram)

    session.commit()


def recalc_idfs(session, grams=None):
    """Re-calculate idfs for database.

    calculating idfs for gram is taking long time.
    So I made it calculates idfs for some grams.
    If you want make accuracy higher, use this with grams=None.

    :param session: DB session
    :type session: :class:`sqlalchemt.orm.Session`

    :param grams: grams that you want to re-calculating idfs
    :type grams: A set of :class:`Gram`

    """
    session.begin(subtransactions=True)

    if not grams:
        grams = session.query(Gram).all()
    for gram in grams:
        gram.idf = _get_idf(session, gram)

    session.commit()


def get_count(session):
    """Get count of :class:`Document`.

    :param session: DB session
    :type session: :class:`sqlalchemt.orm.Session`

    """
    return session.query(Document).count()


def _get_grams(session, text, make=False):
    grams = set()
    session.begin(subtransactions=True)

    if len(text) < GRAM_LENGTH:
        gram_obj = session.query(Gram).filter_by(gram=text).first()
        if gram_obj:
            grams.add(gram_obj)
        elif make:
            gram_obj = Gram(text)
            session.add(gram_obj)
            grams.add(gram_obj)
    else:
        for i in range(len(text) - GRAM_LENGTH + 1):
            gram = text[i:i+GRAM_LENGTH]
            gram_obj = session.query(Gram).filter_by(gram=gram).first()
            if gram_obj:
                grams.add(gram_obj)
            elif make:
                gram_obj = Gram(gram)
                session.add(gram_obj)
                grams.add(gram_obj)

    session.commit()
    return grams


def _get_tf(gram, document):
    if isinstance(gram, Gram):
        gram = gram.gram

    if isinstance(gram, buffer):
        gram = str(gram)
    if not isinstance(gram, unicode):
        gram = gram.decode('utf-8')

    return document.text.count(gram) + document.answer.count(gram)


def _get_idf(session, gram):
    all_count = session.query(Document).count()
    d_count = len(gram.documents)
    return math.log((all_count / (1.0 + d_count)) + 1)


def _get_tf_idfs(self, document):
    tf_idfs = dict(
        (gram.gram, _get_tf(gram, document) * gram.idf)
        for gram in document.grams
        if gram.idf is not None)
    return tf_idfs


def _cosine_measure(v1, v2):
    intersection = set(v1.keys()) & set(v2.keys())
    numerator = sum([v1[x] * v2[x] for x in intersection])

    sum1 = sum([v1[x]**2 for x in v1.keys() if v1[x] is not None])
    sum2 = sum([v2[y]**2 for y in v2.keys() if v2[y] is not None])

    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    try:
        return numerator / denominator
    except ZeroDivisionError:
        return 0


class NoAnswerError(Exception):
    """Raises when autotweet can not found best answer to a question.

    :param msg: A message for the exception
    :type msg: :class:`str`

    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
