import logging
import math
import random
from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker


__all__ = ('Document', 'Gram', 'init_db', 'get_session', 'add_document',
           'get_best_answer', 'recreate_grams', 'recalc_idfs')


Base = declarative_base()
GRAM_LENGTH = 2

logger = logging.getLogger('database')


association_table = Table(
    'association', Base.metadata,
    Column('gram_id', Integer, ForeignKey('grams.id')),
    Column('document_id', Integer, ForeignKey('documents.id'))
    )


class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    text = Column(String(140), nullable=False)
    answer = Column(String(140), nullable=False)
    grams = relationship(
        'Gram', secondary=association_table, backref='documents')

    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Gram(Base):
    __tablename__ = 'grams'
    id = Column(Integer, primary_key=True)
    gram = Column(String(GRAM_LENGTH), unique=True, nullable=False)
    idf = Column(Integer)

    def __init__(self, gram):
        self.gram = gram


def init_db(url):
    engine = create_engine(url)
    db_session = scoped_session(
        sessionmaker(engine))
    Base.metadata.create_all(engine)
    Base.query = db_session.query_property()
    db_session.close()


def get_session(url):
    engine = create_engine(url)
    db_session = scoped_session(
        sessionmaker(engine, autoflush=True, autocommit=True))
    return db_session


def add_document(session, question, answer):
    question = question.strip()
    answer = answer.strip()

    if session.query(Document)\
            .filter_by(text=question, answer=answer).count():
        logger.info(u'Already here: {0} -> {1}'.format(question, answer))
        return
    logger.info(u'add document: {0} -> {1}'.format(question, answer))

    session.begin()

    grams = _get_grams(session, question, make=True)

    doc = Document(question, answer)
    doc.grams = list(grams)
    recalc_idfs(session, grams)

    session.add(doc)
    session.commit()


def get_best_answer(session, query):
    if not isinstance(query, unicode):
        query = query.decode('utf-8')

    if len(query) < GRAM_LENGTH:
        return

    session.begin()

    grams = _get_grams(session, query)
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
        return None


def recreate_grams(session):
    session.begin()

    for document in session.query(Document).all():
        grams = _get_grams(session, document.text, make=True)
        document.grams = list(grams)

    broken_links = session.query(Gram)\
        .filter(~Gram.documents.any()).all()
    for gram in broken_links:
        session.delete(gram)

    session.commit()


def recalc_idfs(session, grams=None):
    session.begin(subtransactions=True)

    if not grams:
        grams = session.query(Gram).all()
    for gram in grams:
        gram.idf = _get_idf(session, gram)

    session.commit()


def get_count(session):
    return session.query(Document).count()


def _get_grams(session, text, make=False):
    grams = set()
    session.begin(subtransactions=True)

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
