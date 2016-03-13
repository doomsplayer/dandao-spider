"""
Here defines all the models used by qzz
"""
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr

ENGINE = create_engine('sqlite:///dandao.db', echo=True)
Session = sessionmaker(bind=ENGINE)

def create_db():
    Base.metadata.create_all(ENGINE)

class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

Base = declarative_base(cls=Base)

class User(Base):
    uid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return "<User(uid={}, name={}, posts={})>".format(self.uid, self.name, len(self.posts))

class Group(Base):
    gid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return "<Group(gid={}, name={}, fields={})>".format(self.gid, self.name, self.fields.map(lambda x: x.name))

class Forum(Base):
    fid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    updated_at = Column(DateTime)

    group_id = Column(Integer, ForeignKey(Group.gid), nullable=False)
    group = relationship(Group, backref="fields")

    def __repr__(self):
        return "<Field(fid={}, name={}, group={}, threads={})>".format(self.fid, self.name, self.grid.name, len(self.threads))

class Thread(Base):
    tid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    forum_id = Column(Integer, ForeignKey(Forum.fid), nullable=False)
    forum = relationship(Forum, backref="threads")

    def __repr__(self):
        return "<Thread(tid={}, name={}, field={}, posts={})>".format(self.tid, self.name, self.field.name, len(self.posts))

class Post(Base):
    pid = Column(Integer, primary_key=True)
    content = Column(String)
    updated_at = Column(DateTime)
    created_at = Column(DateTime)

    user_id = Column(Integer, ForeignKey(User.uid), nullable=False)
    user = relationship(User, backref="posts")

    thread_id = Column(Integer, ForeignKey(Thread.tid), nullable=False)
    thread = relationship(Thread, backref="posts")

    def __repr__(self):
        return "<Post(id={}, user={}, thread={}, content={})>".format(self.id, self.user.name, self.thread.name, self.content)

