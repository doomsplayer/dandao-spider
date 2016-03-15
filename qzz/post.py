"""Here defines the Post model"""
import regex

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from multipledispatch import Dispatcher
from pyquery import PyQuery
from dateutil.parser import parse as dateparse
import logging

from . import Base, DbSession, session_scope
from .client import Client
from .thread import Thread
from .user import User
from .forum import Forum
from .group import Group

DISPATCHER = Dispatcher("post")
def dispatch(*types):
    def wrapper(func):
        DISPATCHER.add(types, func)
        return DISPATCHER
    return wrapper

class Post(Base):
    """The Post model"""
    pid = Column(Integer, primary_key=True)
    content = Column(String)
    updated_at = Column(DateTime)
    created_at = Column(DateTime)

    user_id = Column(Integer, ForeignKey(User.uid), nullable=False)
    user = relationship(User, backref="posts")

    thread_id = Column(Integer, ForeignKey(Thread.tid), nullable=False)
    thread = relationship(Thread, backref="posts")

    def __repr__(self):
        return "<Post(pid={}, user={}, thread={}, content={})>".format(self.pid, self.user.name, self.thread.name, self.content)

    @staticmethod
    @dispatch(PyQuery)
    def pages(query):
        pages = 1
        paginator = query.find("#ct > div.pgs.mtm.mbm.cl > div > label > span").attr("title")
        if paginator:
            reg = regex.compile(r"共 +(\d+) +页")
            result = reg.findall(paginator)
            pages = int(result[0])
        return pages

    @staticmethod
    @dispatch(Client, int, int)
    def post_page(client, tid, page):
        resp = client.get("forum.php?mod=viewthread&tid={}&page={}".format(tid, page))
        query = PyQuery(resp.text)
        return query

    @staticmethod
    @dispatch(Client, Thread, object)
    def update_posts(client, thread, session):
        logging.info("Updating posts list for {}".format(thread))
        query = Post.post_page(client, thread.tid, 1)

        reg_uid = regex.compile(r"^home\.php\?mod=space&uid=(\d+)$")
        reg_pid = regex.compile(r"^post_(\d+)$")
        reg_update = regex.compile(r"本帖最后由 .*? 于 (.+) 编辑")
        pages = Post.pages(query)
        logging.info("Total {} pages for {}".format(pages, thread))
        for i in range(1, pages+1):
            logging.info("Fetching {} page {}".format(thread, i))
            query = Post.post_page(client, thread.tid, i).find("#postlist")

            for div in query.find("div"):
                sub_query = PyQuery(div)
                pid_str = sub_query.attr("id")
                if not pid_str or not reg_pid.match(pid_str):
                    continue

                pid = int(reg_pid.findall(pid_str)[0])

                user_query = sub_query.find("tr>td.pls").find("div.authi>a")
                author_uid = reg_uid.findall(user_query.attr("href"))[0]
                author_username = user_query.text()

                auth_date = dateparse(user_query.find("tr>td.plc>div.pi").find("div.authi>em").text().strip("发表于 "))
                content_query = user_query.find("tr>td.plc>div.pct>div.pcb>div.t_fsz>table").find("td.t_f")
                content = content_query.html()

                update_date = auth_date
                if content_query.find("i.pstatus"):

                    edit_time = content_query.find("i.pstatus").text()
                    update_date = dateparse(reg_update.findall(edit_time)[0])

                author = User(uid=author_uid, name=author_username)
                logging.info("Merging {}".format(author))
                session.merge(author)


                post = Post(pid=pid, content=content, created_at=auth_date, updated_at=update_date, user=author, thread=thread)
                logging.info("Merging {}".format(post))
                session.merge(post)
        thread.fresh = True
        session.add(thread)

    @staticmethod
    @dispatch(Client)
    def update_posts(client):
        with session_scope() as session:
            threads = session.query(Thread).join(Forum).join(Group).filter(Group.gid != 1).filter(Thread.fresh == 0).all()
            for thread in threads:
                Post.update_posts(client, thread, session)

