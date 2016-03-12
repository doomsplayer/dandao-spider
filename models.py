from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr

ENGINE = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=ENGINE)

class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

Base = declarative_base(cls=Base)

class User(Base):
    uid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return "<User(uid={}, name={})>".format(self.uid, self.name)

class Grid(Base):
    gid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return "<Grid(gid={}, name={}, fields={})>".format(self.gid, self.name, self.fields.map(lambda x: x.name))

class Field(Base):
    fid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    grid_id = Column(Integer, ForeignKey(Grid.gid), nullable=False)
    grid = relationship(Grid, backref="fields")

    def __repr__(self):
        return "<Field(fid={}, name={}, grid={}, threads={})>".format(self.fid, self.name, self.grid.name, len(self.threads))

class Thread(Base):
    tid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    field_id = Column(Integer, ForeignKey(Field.fid), nullable=False)
    field = relationship(Field, backref="threads")

    def __repr__(self):
        return "<Thread(tid={}, name={}, field={}, layers={})>".format(self.tid, self.name, self.field.name, len(self.layers))

class Layer(Base):
    id = Column(Integer, primary_key=True)
    content = Column(String)

    user_id = Column(Integer, ForeignKey(User.uid), nullable=False)
    user = relationship(User, backref="layers")

    thread_id = Column(Integer, ForeignKey(Thread.tid), nullable=False)
    thread = relationship(Thread, backref="layers")

    def __repr__(self):
        return "<Layer(id={}, user={}, thread={}, content={})>".format(self.id, self.user.name, self.thread.name, self.content)

