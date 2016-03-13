"""
A custom http client with cookie
"""
import requests
import regex
from pyquery import PyQuery
from multipledispatch import dispatch
from models import Group, Forum, User, Thread, Post, Session, ENGINE
from dateutil.parser import parse as dateparse

class Client:
    def __init__(self, username, password, url="http://bbs.dandao.net"):
        self.username = username
        self.password = password
        self.url = url.strip("/") + "/"
        self.s = requests.Session()

    def login(self):
        resp = self.s.get(self.url)
        document = PyQuery(resp.text)
        form = document.find("form#lsform")
        login_url = self.url + form.attr("action")
        data = {
            "username": self.username,
            "password": self.password,
            "handlekey": "ls",
            "quickforward": "yes",
        }
        resp = self.s.post(login_url, data=data)
        query = PyQuery(resp.text)
        resp_username = query.find("strong.vwmy>a").text()
        if resp_username != self.username:
            alert = query.find("div#messagetext.alert_error>p").text()
            raise RuntimeError("Login failed: {}".format(alert))

    def fetch_all_groups(self):
        url = self.url + "forum.php"
        resp = self.s.get(url)
        query = PyQuery(resp.text)
        reg = regex.compile(r"^forum\.php\?gid=(\d+)$")
        gids = [(a.attrib["href"], a.text) for a in query.find("div.bm_h.cl>h2>a")]
        gids = [(int(gid), name) for (git, name) in gids for gid in reg.findall(git)]
        session = Session()

        groups = [Group(name=name, gid=gid) for (gid, name) in gids]
        for group in groups:
            session.merge(group)
        session.commit()

    @dispatch()
    def fetch_all_forums(self):
        session = Session()
        groups = session.query(Group).all()
        for group in groups:
            self.fetch_all_forums(group)

    @dispatch(Group)
    def fetch_all_forums(self, group):
        url = self.url + "forum.php?gid={}".format(group.gid)
        resp = self.s.get(url)
        query = PyQuery(resp.text)
        reg = regex.compile(r"^forum\.php\?mod=forumdisplay&fid=(\d+)$")

        models = []
        for row in query.find("table.fl_tb>tr"):
            q = PyQuery(row)
            href = q.find("td").eq(1).find("a").attr("href")
            if not href:
                continue

            fid = int(reg.findall(href)[0])

            name = q.find("td").eq(1).find("h2>a").clone().children().remove().end().text()
            last_update = q.find("td").eq(3).find("div>cite").clone().children().remove().end().text()
            last_update = dateparse(last_update)
            forum = Forum(fid=fid, name=name, updated_at=last_update)
            models.append(forum)

        session = Session()
        for forum in models:
            forum.group = group
            session.merge(forum)
        session.commit()

    @dispatch(Forum)
    def fetch_all_threads(self, forum):
        url = self.url + "forum.php?mod=forumdisplay&fid={}".format(forum.fid)
        resp = self.s.get(url)
        query = PyQuery(resp.text)
        paginator = query.find("#fd_page_bottom > div > label > span").attr("title")
        pages = 1
        if paginator:
            reg = regex.compile(r"共 (\d+) 页")
            result = reg.findall(paginator)
            pages = int(result[0])

        session = Session()
        print(pages)
        for i in range(1, pages+1):
            url = self.url + "forum.php?mod=forumdisplay&fid={}&page={}".format(forum.fid, i)
            resp = self.s.get(url)
            query = PyQuery(resp.text).find("#threadlisttableid")

            reg_uid = regex.compile(r"^home\.php\?mod=space&uid=(\d+)$")
            reg_tid = regex.compile(r"^normalthread_(\d+)$")

            for tbody in query.find("tbody"):
                q = PyQuery(tbody)
                id = q.attr("id")
                if not id or not reg_tid.match(id): continue

                tid = int(reg_tid.findall(id)[0])
                name = q.find("th>a.s.xst").text()

                userq = q.find("td.by").eq(0)
                author_uid = reg_uid.findall(userq.find("cite>a").attr("href"))[0]
                author_username = userq.find("cite>a").text()
                author_date = dateparse(userq.find("em>span").text())

                userq = q.find("td.by").eq(1)
                #replier_uid = reg_uid.findall(userq.find("cite>a").attr("href"))[0]
                #replier_username = userq.find("cite>a").text()
                reply_date = dateparse(userq.find("em>a").text())

                author = User(uid=author_uid, name=author_username)
                session.merge(author)

                thread = Thread(tid=tid, name=name, created_at=author_date, updated_at=reply_date, forum=forum)
                session.merge(thread)
        session.commit()

    @dispatch()
    def fetch_all_threads(self):
        session = Session()
        forums = session.query(Forum).all()
        for forum in forums:
            self.fetch_all_threads(forum)

    @dispatch(Thread)
    def fetch_all_posts(self, thread):
        url = self.url + "forum.php?mod=viewthread&tid={}".format(thread.tid)
        resp = self.s.get(url)
        query = PyQuery(resp.text)
        paginator = query.find("#ct > div.pgs.mtm.mbm.cl > div > label > span").attr("title")
        pages = 1
        if paginator:
            reg = regex.compile(r"共 (\d+) 页")
            result = reg.findall(paginator)
            pages = int(result[0])

        session = Session()

        for i in range(1, pages+1):
            url = self.url + "forum.php?mod=viewthread&tid={}&page={}".format(thread.tid, i)
            resp = self.s.get(url)
            query = PyQuery(resp.text).find("#postlist")

            reg_uid = regex.compile(r"^home\.php\?mod=space&uid=(\d+)$")
            reg_pid = regex.compile(r"^post_(\d+)$")
            reg_update = regex.compile(r"本帖最后由 .*? 于 (.+) 编辑")
            for div in query.find("div"):
                q = PyQuery(div)
                id = q.attr("id")
                if not id or not reg_pid.match(id): continue

                pid = int(reg_pid.findall(id)[0])

                userq = q.find("tr>td.pls").find("div.authi>a")
                author_uid = reg_uid.findall(userq.attr("href"))[0]
                author_username = userq.text()

                auth_date = dateparse(q.find("tr>td.plc>div.pi").find("div.authi>em").text().strip("发表于 "))
                contentq = q.find("tr>td.plc>div.pct>div.pcb>div.t_fsz>table").find("td.t_f")
                content = contentq.html()

                update_date = auth_date
                if contentq.find("i.pstatus"):
                    edit_time = contentq.find("i.pstatus").text()
                    update_date = dateparse(reg_update.findall(edit_time)[0])

                author = User(uid=author_uid, name=author_username)
                session.merge(author)

                post = Post(pid=pid, content=content, created_at=auth_date, updated_at=update_date, user=author, thread=thread)
                session.merge(post)
        session.commit()

    @dispatch()
    def fetch_all_posts(self):
        session = Session()
        threads = session.query(Thread).join(Forum).join(Group).filter(Group.gid != 1).all()
        for thread in threads:
            self.fetch_all_posts(thread)

            
