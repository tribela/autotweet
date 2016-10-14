""":mod:`autotweet.database` --- Database structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides methods to get session, get answer, etc.

"""
from __future__ import unicode_literals
import logging
from sqlalchemy import (Column, Float,  ForeignKey, Integer, String, Table,
                        UniqueConstraint, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker


__all__ = ('Base', 'Document', 'Gram', 'get_session')

Base = declarative_base()
GRAM_LENGTH = 2

logger = logging.getLogger('database')


def get_session(url):
    """Get db session.

    :param url: URL for connect with DB
    :type url: :class:`str`

    :returns: A sqlalchemy db session
    :rtype: :class:`sqlalchemy.orm.Session`

    """
    engine = create_engine(url)
    db_session = scoped_session(sessionmaker(engine))
    Base.metadata.create_all(engine)
    return db_session


association_table = Table(
    'association', Base.metadata,
    Column('gram_id', Integer, ForeignKey('grams.id')),
    Column('document_id', Integer, ForeignKey('documents.id'))
    )


class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = (
        UniqueConstraint('text', 'answer'),
    )
    id = Column(Integer, primary_key=True)
    text = Column(String(140), nullable=False)
    answer = Column(String(140), nullable=False)
    grams = relationship(
        'Gram', secondary=association_table, backref='documents')

    __table_args__ = (UniqueConstraint('text', 'answer'),)

    def __init__(self, text, answer):
        self.text = text
        self.answer = answer


class Gram(Base):
    __tablename__ = 'grams'
    id = Column(Integer, primary_key=True)
    gram = Column(String(GRAM_LENGTH), unique=True, nullable=False)
    idf = Column(Float)

    def __init__(self, gram):
        self.gram = gram
