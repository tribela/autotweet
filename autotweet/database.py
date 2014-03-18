from aqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
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
        'Gram', secondary_association_table, backref='documents')

    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Gram(Base):
    __tablename__ = 'grams'
    id = Column(Integer, primary_key=True)
    gram = Column(String, unique=True, nullable=False)

    def __init__(self, gram):
        self.gram = gram


def init_db(url):
    engine = create_engine(url)
    db_session = scoped_session(sessionmaker(engine))
    Base.metadata.create_all(engine)

    return db_session


def add_document(session, question, answer):
    grams = set()
    for i in range(len(question - GRAM_LENGTH + 1)):
        gram = question[i:i+GRAM_LENGTH]
        gram = session.query(Gram).filter_by(gram=gram).first() or Gram(gram)
        session.add(Gram)
        grams.add(gram)

    doc = Document(question, answer)
    doc.grams = grams

    session.commit()
