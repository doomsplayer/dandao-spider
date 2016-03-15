"""Here defines the forum model"""
import regex

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from multipledispatch import dispatch
from pyquery import PyQuery
from dateutil.parser import parse as dateparse
import logging

from . import Base, DbSession, session_scope
from .group import Group
from .client import Client

class Forum(Base):
    """Here defines the forum model"""
    fid = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    updated_at = Column(DateTime)

    group_id = Column(Integer, ForeignKey(Group.gid), nullable=False)
    group = relationship(Group, backref="fields")

    fresh = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return "<Forum(fid={}, name={}, group={}, threads={})>".format(self.fid, self.name, self.group.name, len(self.threads))

    @staticmethod
    @dispatch(Client, int)
    def get_forum_page(client, gid):
        resp = client.get("forum.php?gid={}".format(gid))
        query = PyQuery(resp.text)
        return query

    @staticmethod
    @dispatch(Client, Group, object)
    def update_forums(client, group, session):
        logging.info("Updating forums list for {}".format(group))
        query = Forum.get_forum_page(client, group.gid)
        reg = regex.compile(r"^forum\.php\?mod=forumdisplay&fid=(\d+)$")

        for row in query.find("table.fl_tb>tr"):
            sub_query = PyQuery(row)
            href = sub_query.find("td").eq(1).find("a").attr("href")
            if not href:
                continue

            fid = int(reg.findall(href)[0])

            name = sub_query.find("td").eq(1).find("h2>a").clone().children().remove().end().text()
            last_update = sub_query.find("td").eq(3).find("div>cite").clone().children().remove().end().text()
            last_update = dateparse(last_update)

            existence = session.query(Forum).filter(Forum.fid == fid)
            if existence.count() == 0:
                logging.info("<Forum(fid={})> not found, creating one".format(fid))
                forum = Forum(fid=fid, name=name, updated_at=last_update, group=group, fresh=False)
                session.add(forum)
            else:
                forum = existence.one()
                if forum.updated_at != last_update:
                    logging.info("{} found, stale: against {} ".format(forum, last_update))
                    forum.updated_at = last_update
                    forum.fresh = False
                    session.add(forum)
                else:
                    logging.info("{} found, fresh".format(forum))

    @staticmethod
    @dispatch(Client)
    def update_forums(client):
        with session_scope() as session:
            groups = session.query(Group).all()
            for group in groups:
                Forum.update_forums(client, group, session)

