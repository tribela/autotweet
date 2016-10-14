from __future__ import unicode_literals
import logging
import math
import random

from .database import GRAM_LENGTH, Document, Gram, get_session


__all__ = ('NoAnswerError', 'DataCollection')

logger = logging.getLogger('learning')


class DataCollection(object):

    def __init__(self, db_url):
        self.session = get_session(db_url)

    def add_document(self, question, answer):
        """Add question answer set to DB.

        :param question: A question to an answer
        :type question: :class:`str`

        :param answer: An answer to a question
        :type answer: :class:`str`

        """
        question = question.strip()
        answer = answer.strip()

        if self.session.query(Document) \
                .filter_by(text=question, answer=answer).count():
            logger.info('Already here: {0} -> {1}'.format(question, answer))
            return
        logger.info('add document: {0} -> {1}'.format(question, answer))

        grams = self._get_grams(question, make=True)

        doc = Document(question, answer)
        doc.grams = list(grams)
        self._recalc_idfs(grams)

        self.session.add(doc)
        self.session.commit()
        self.session.close()

    def get_best_answer(self, query):
        """Get best answer to a question.

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

        grams = self._get_grams(query)
        if not grams:
            raise NoAnswerError('Can not found answer')

        documents = set([doc for gram in grams for doc in gram.documents])

        self._recalc_idfs(grams)

        idfs = dict((gram.gram, gram.idf) for gram in grams)

        docs = dict(
            (doc.answer, _cosine_measure(idfs, self._get_tf_idfs(doc)))
            for doc in documents)
        docs = dict((key, val) for (key, val) in docs.items() if val)

        self.session.commit()

        try:
            max_ratio = max(docs.values())
            answers = [answer for answer in docs.keys()
                       if docs.get(answer) == max_ratio]

            answer = random.choice(answers)
            logger.debug('{0} -> {1} ({2})'.format(query, answer, max_ratio))
            return (answer, max_ratio)
        except ValueError:
            raise NoAnswerError('Can not found answer')
        finally:
            self.session.close()

    def recreate_grams(self):
        """Re-create grams for database.

        In normal situations, you never need to call this method.
        But after migrate DB, this method is useful.

        :param session: DB session
        :type session: :class:`sqlalchemt.orm.Session`

        """

        for document in self.session.query(Document).all():
            grams = self._get_grams(document.text, make=True)
            document.grams = list(grams)

        broken_links = self.session.query(Gram) \
            .filter(~Gram.documents.any()).all()
        for gram in broken_links:
            self.session.delete(gram)

        self.session.commit()
        self.session.close()

    def recalc_idfs(self, grams=None):
        self._recalc_idfs(grams)
        self.session.close()

    def _recalc_idfs(self, grams=None):
        """Re-calculate idfs for database.

        calculating idfs for gram is taking long time.
        So I made it calculates idfs for some grams.
        If you want make accuracy higher, use this with grams=None.

        :param session: DB session
        :type session: :class:`sqlalchemt.orm.Session`

        :param grams: grams that you want to re-calculating idfs
        :type grams: A set of :class:`Gram`

        """

        if not grams:
            grams = self.session.query(Gram).all()
        for gram in grams:
            gram.idf = self._get_idf(gram)

    def get_count(self):
        """Get count of :class:`Document`.

        :param session: DB session
        :type session: :class:`sqlalchemt.orm.Session`

        """
        return self.session.query(Document).count()

    def _get_grams(self, text, make=False):
        grams = set()
        self.session.begin(subtransactions=True)

        if len(text) < GRAM_LENGTH:
            gram_obj = self.session.query(Gram).filter_by(gram=text).first()
            if gram_obj:
                grams.add(gram_obj)
            elif make:
                gram_obj = Gram(text)
                self.session.add(gram_obj)
                grams.add(gram_obj)
        else:
            for i in range(len(text) - GRAM_LENGTH + 1):
                gram = text[i:i+GRAM_LENGTH]
                gram_obj = self.session.query(Gram).filter_by(gram=gram).first()
                if gram_obj:
                    grams.add(gram_obj)
                elif make:
                    gram_obj = Gram(gram)
                    self.session.add(gram_obj)
                    grams.add(gram_obj)

        self.session.commit()
        return grams

    @staticmethod
    def _get_tf(gram, document):
        if isinstance(gram, Gram):
            gram = gram.gram

        if isinstance(gram, buffer):
            gram = str(gram)
        if not isinstance(gram, unicode):
            gram = gram.decode('utf-8')

        return document.text.count(gram) + document.answer.count(gram)

    def _get_idf(self, gram):
        all_count = self.session.query(Document).count()
        d_count = len(gram.documents)
        return math.log((all_count / (1.0 + d_count)) + 1)

    def _get_tf_idfs(self, document):
        tf_idfs = dict(
            (gram.gram, self._get_tf(gram, document) * gram.idf)
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
