import logging
import math
import random
from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
GRAM_LENGTH = 2


association_table = Table(
    'association', Base.metadata,
    Column('gram_id', Integer, ForeignKey('grams.id')),
    Column('document_id', Integer, ForeignKey('documents.id'))
    )


class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    grams = relationship(
        'Gram', secondary=association_table, backref='documents')

    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Gram(Base):
    __tablename__ = 'grams'
    id = Column(Integer, primary_key=True)
    gram = Column(String, unique=True, nullable=False)
    idf = Column(Integer)

    def __init__(self, gram):
        self.gram = gram


class AutoAnswer():

    def __init__(self, url):
        engine = create_engine(url)
        db_session = scoped_session(sessionmaker(engine))
        Base.metadata.create_all(engine)
        self.session = db_session

    def add_document(self, question, answer):
        if self.session.query(Document)\
                .filter_by(text=question, answer=answer).count():
            logging.info(u'Already here: {0} -> {1}'.format(question, answer))
            return
        logging.info(u'add document: {0} -> {1}'.format(question, answer))
        self._add_doc(question, answer)

    def get_best_answer(self, query):
        if not isinstance(query, unicode):
            query = query.decode('utf-8')

        if len(query) < GRAM_LENGTH:
            return

        docs = {}
        grams = self._get_grams(query)
        self._recalc_idfs(grams)

        idfs = dict((gram.gram, gram.idf) for gram in grams)

        documents = set([doc for gram in grams for doc in gram.documents])
        docs = dict(
            (doc.answer, self._cosine_measure(idfs, self._get_tf_idfs(doc)))
            for doc in documents)
        docs = dict((key, val) for (key, val) in docs.items() if val)

        try:
            max_ratio = max(docs.values())
            answers = [answer for answer in docs.keys()
                       if docs.get(answer) == max_ratio]

            answer = random.choice(answers)
            logging.debug(u'{0} -> {1} ({2})'.format(query, answer, max_ratio))
            return (answer, max_ratio)
        except ValueError:
            return None

    def recreate_grams(self):
        for document in self.session.query(Document).all():
            grams = self._get_grams(document.text, make=True)
            document.grams = list(grams)

        self.session.commit()

        broken_links = self.session.query(Gram)\
                .filter(~Gram.documents.any()).all()
        for gram in broken_links:
            self.session.delete(gram)

        self.session.commit()

    def _add_doc(self, question, answer):
        question = question.strip()
        answer = answer.strip()
        if self.session.query(Document)\
                .filter_by(text=question, answer=answer).count():
            return

        grams = self._get_grams(question, make=True)

        doc = Document(question, answer)
        doc.grams = list(grams)

        self.session.commit()

    def _recalc_idfs(self, grams=None):
        if not grams:
            grams = self.session.query(Gram).all()
        for gram in grams:
            gram.idf = self._get_idf(gram)

        self.session.commit()

    def _get_grams(self, text, make=False):
        grams = set()
        for gram in self._segmentize(text, GRAM_LENGTH):
            gram_obj = self.session.query(Gram).filter_by(gram=gram).first()
            if gram_obj:
                grams.add(gram_obj)
            elif make:
                gram_obj = Gram(gram)
                self.session.add(gram_obj)
                grams.add(gram_obj)

        return grams

    def _segmentize(self, text, length):
        segments = []
        for word in text.split():
            segments += [word[i:i+length]
                         for i in range(len(word) - length + 1)]
        return segments

    def _get_tf(self, gram, document):
        if isinstance(gram, Gram):
            gram = gram.gram

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

    def _cosine_measure(self, v1, v2):
        intersection = set(v1.keys()) & set(v2.keys())
        numerator = sum([v1[x] * v2[x] for x in intersection])

        sum1 = sum([v1[x]**2 for x in v1.keys() if v1[x] is not None])
        sum2 = sum([v2[y]**2 for y in v2.keys() if v2[y] is not None])

        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0

    def __len__(self):
        return self.session.query(Document).count()
