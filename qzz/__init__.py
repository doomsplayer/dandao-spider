"""Here defines all the models used by qzz"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr

ENGINE = create_engine('sqlite:///dandao.db', echo=False)
DbSession = sessionmaker(bind=ENGINE)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = DbSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def create_db():
    """Create the database"""
    Base.metadata.create_all(ENGINE)

class Base:
    """The base class for all models"""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

Base = declarative_base(cls=Base)

from .forum import Forum
from .group import Group
from .post import Post
from .client import Client
from .thread import Thread

