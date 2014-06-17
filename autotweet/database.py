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


class AutoAnswer():

    def __init__(self, url):
        engine = create_engine(url)
        db_session = scoped_session(sessionmaker(engine))
        Base.metadata.create_all(engine)
        self.session = db_session

    def add_document(self, question, answer):
        self._add_doc(question, answer)
        self._recalc_idfs()

    def get_best_answer(self, query):
        grams = set()
        docs = {}
        if not isinstance(query, unicode):
            query = query.decode('utf-8')
        for i in range(len(query) - GRAM_LENGTH + 1):
            gram = query[i:i+GRAM_LENGTH]
            gram = self.session.query(Gram).filter_by(gram=gram).first()
            if gram:
                grams.add(gram)

        idfs = dict((gram.gram, gram.idf) for gram in grams)

        documents = self.session.query(Document).all()
        docs = dict(
            (doc.answer, self._cosine_measure(idfs, self._get_tf_idfs(doc)))
            for doc in documents)
        docs = dict((key, val) for (key, val) in docs.items() if val)

        try:
            key = max(docs, key=docs.get)
            return (key, docs[key])
        except ValueError:
            return None

    def recreate_grams(self):
        for document in self.session.query(Document).all():
            grams = self._make_grams(document.text)
            document.grams = list(grams)

        self.session.commit()

        self._recalc_idfs()

    def _add_doc(self, question, answer):
        question = question.strip()
        answer = answer.strip()
        if self.session.query(Document)\
                .filter_by(text=question, answer=answer).count():
            return

        grams = self._make_grams(question)

        doc = Document(question, answer)
        doc.grams = list(grams)

        self.session.commit()

    def _recalc_idfs(self):
        for gram in self.session.query(Gram).all():
            gram.idf = self._get_idf(gram)

        self.session.commit()

    def _make_grams(self, text):
        grams = set()
        for i in range(len(text) - GRAM_LENGTH + 1):
            gram = text[i:i+GRAM_LENGTH]
            gram = self.session.query(Gram)\
                .filter_by(gram=gram).first() or Gram(gram)
            self.session.add(gram)
            grams.add(gram)

        return grams

    def _get_tf(self, gram, document):
        if isinstance(gram, Gram):
            gram = gram.gram

        return document.text.count(gram)

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

        sum1 = sum([v1[x]**2 for x in v1.keys()])
        sum2 = sum([v2[y]**2 for y in v2.keys()])

        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0

    def __len__(self):
        return self.session.query(Document).count()
