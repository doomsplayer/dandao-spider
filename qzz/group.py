"""Here defines the group model"""
import regex

from sqlalchemy import Column, Integer, String
from multipledispatch import dispatch
from pyquery import PyQuery

from . import Base, DbSession, session_scope
from .client import Client

class Group(Base):
    """The group model"""
    gid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return "<Group(gid={}, name={}, fields={})>".format(self.gid, self.name, [x.name for x in self.fields])

    @staticmethod
    @dispatch(Client)
    def get_group_page(client):
        resp = client.get("forum.php")
        query = PyQuery(resp.text)
        return query

    @staticmethod
    @dispatch(Client, object)
    def update_groups(client, session):
        query = Group.get_group_page(client)

        reg = regex.compile(r"^forum\.php\?gid=(\d+)$")
        gids = [(a.attrib["href"], a.text) for a in query.find("div.bm_h.cl>h2>a")]
        gids = [(int(gid), name) for (git, name) in gids for gid in reg.findall(git)]

        groups = [Group(name=name, gid=gid) for (gid, name) in gids]
        for group in groups:
            session.merge(group)

    @staticmethod
    @dispatch(Client)
    def update_groups(client):
        with session_scope() as session:
            Group.update_groups(client, session)
