import math
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


def init_db(url):
    engine = create_engine(url)
    db_session = scoped_session(sessionmaker(engine))
    Base.metadata.create_all(engine)

    return db_session


def add_document(session, question, answer):
    _add_doc(session, question, answer)
    _recalc_idfs(session)


def _add_doc(session, question, answer):
    if session.query(Document, text=question, answer=answer).count():
        return

    grams = set()
    for i in range(len(question) - GRAM_LENGTH + 1):
        gram = question[i:i+GRAM_LENGTH]
        gram = session.query(Gram).filter_by(gram=gram).first() or Gram(gram)
        session.add(gram)
        grams.add(gram)

    doc = Document(question, answer)
    doc.grams = list(grams)

    session.commit()


def _recalc_idfs(session):
    for gram in session.query(Gram).all():
        gram.idf = get_idf(session, gram)

    session.commit()


def get_tf(gram, document):
    if isinstance(gram, Gram):
        gram = gram.gram

    return document.text.count(gram)


def get_idf(session, gram):
    all_count = session.query(Document).count()
    d_count = len(gram.documents)
    return math.log((all_count / (1.0 + d_count)) + 1)


def get_tf_idfs(document):
    tf_idfs = {}
    for gram in document.grams:
        tf_idfs[gram.gram] = get_tf(gram, document) * gram.idf
    return tf_idfs


def cosine_measure(v1, v2):
    intersection = set(v1.keys()) & set(v2.keys())
    numerator = sum([v1[x] * v2[x] for x in intersection])

    sum1 = sum([v1[x]**2 for x in v1.keys()])
    sum2 = sum([v2[y]**2 for y in v2.keys()])

    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    try:
        return numerator / denominator
    except ZeroDivisionError:
        return 0


def get_best_answer(session, query):
    grams = set()
    docs = {}
    for i in range(len(query) - GRAM_LENGTH + 1):
        gram = query[i:i+GRAM_LENGTH]
        gram = session.query(Gram).filter_by(gram=gram).first()
        if gram:
            grams.add(gram)

    idfs = dict((gram.gram, gram.idf) for gram in grams)

    documents = session.query(Document).all()
    docs = dict((doc.answer, cosine_measure(idfs, get_tf_idfs(doc)))
                for doc in documents)
    docs = dict((key, val) for (key, val) in docs.items() if val)

    try:
        return max(docs, key=docs.get)
    except ValueError:
        return None
