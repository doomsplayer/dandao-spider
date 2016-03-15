"""Here defines the user model"""
from sqlalchemy import Column, Integer, String
from . import Base

class User(Base):
    """The user model"""
    uid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return "<User(uid={}, name={}, posts={})>".format(self.uid, self.name, len(self.posts))
