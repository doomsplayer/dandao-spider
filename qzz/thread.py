"""Here defines the Thread model"""
import regex

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from multipledispatch import Dispatcher
from pyquery import PyQuery
from dateutil.parser import parse as dateparse
import logging

from . import Base, DbSession, session_scope
from .client import Client
from .forum import Forum
from .user import User

DISPATCHER = Dispatcher("thread")
def dispatch(*types):
    def wrapper(func):
        DISPATCHER.add(types, func)
        return DISPATCHER
    return wrapper

class Thread(Base):
    """The Thread model"""
    tid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    forum_id = Column(Integer, ForeignKey(Forum.fid), nullable=False)
    forum = relationship(Forum, backref="threads")

    fresh = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return "<Thread(tid={}, name={}, forum={}, posts={})>".format(self.tid, self.name, self.forum.name, len(self.posts))

    @staticmethod
    @dispatch(PyQuery)
    def pages(query):
        paginator = query.find("#fd_page_bottom > div > label > span").attr("title")
        pages = 1
        if paginator:
            print("a")
            reg = regex.compile(r"共 (\d+) 页")
            result = reg.findall(paginator)
            pages = int(result[0])
        return pages

    @staticmethod
    @dispatch(Client, int, int)
    def thread_page(client, fid, page):
        resp = client.get("forum.php?mod=forumdisplay&fid={}&page={}".format(fid, page))
        query = PyQuery(resp.text)
        return query

    @staticmethod
    @dispatch(Client, Forum, object)
    def update_threads(client, forum, session):
        logging.info("Updating threads list for {}".format(forum))
        query = Thread.thread_page(client, forum.fid, 1)

        reg_uid = regex.compile(r"^home\.php\?mod=space&uid=(\d+)$")
        reg_tid = regex.compile(r"^normalthread_(\d+)$")
        pages = Thread.pages(query)
        logging.info("Total {} pages for {}".format(pages, forum))
        for i in range(1, pages+1):
            logging.info("Fetching {} page {}".format(forum, i))
            query = Thread.thread_page(client, forum.fid, i).find("#threadlisttableid")

            for tbody in query.find("tbody"):
                sub_query = PyQuery(tbody)
                tid_str = sub_query.attr("id")
                if not tid_str or not reg_tid.match(tid_str):
                    continue

                tid = int(reg_tid.findall(tid_str)[0])
                name = sub_query.find("th>a.s.xst").text()

                user_query = sub_query.find("td.by").eq(0)
                author_uid = reg_uid.findall(user_query.find("cite>a").attr("href"))[0]
                author_username = user_query.find("cite>a").text()
                author_date = dateparse(user_query.find("em>span").text())

                user_query = sub_query.find("td.by").eq(1)
                #replier_uid = reg_uid.findall(userq.find("cite>a").attr("href"))[0]
                #replier_username = userq.find("cite>a").text()
                reply_date = dateparse(user_query.find("em>a").text())

                author = User(uid=author_uid, name=author_username)
                session.merge(author)

                existence = session.query(Thread).filter(Thread.tid == tid)
                if existence.count() == 0:
                    logging.info("<Thread(tid={})> not found, creating one".format(tid))
                    thread = Thread(
                        tid=tid,
                        name=name,
                        created_at=author_date,
                        updated_at=reply_date,
                        forum=forum,
                        fresh=False
                    )
                    session.add(thread)
                else:
                    thread = existence.one()
                    if thread.updated_at != reply_date:
                        logging.info("{} found, stale: against {}".format(thread, reply_date))
                        thread.updated_at = reply_date
                        thread.fresh = False
                        session.add(forum)
                    else:
                        logging.info("{} found, fresh".format(thread))

        forum.fresh = True
        session.add(forum)

    @staticmethod
    @dispatch(Client)
    def update_threads(client):
        with session_scope() as session:
            forums = session.query(Forum).filter(Forum.fresh == 0).all()
            for forum in forums:
                Thread.update_threads(client, forum, session)

