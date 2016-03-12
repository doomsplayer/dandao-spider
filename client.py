"""
A custom http client with cookie
"""
import requests
from pyquery import PyQuery
from multipledispatch import dispatch

class Client:
    def __init__(self, username, password, url="http://bbs.dandao.net"):
        self.username = username
        self.password = password
        self.url = url
        self.s = requests.Session()

    def login(self):
        resp = self.s.get(self.url)
        document = PyQuery(resp.text)
        form = document.find("form#lsform")
        login_url = self.url.strip("/") + "/" + form.attr("action")
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

    @dispatch(str)
    def get(self, url, **kwargs):
        return self.s.get(url, **kwargs)

    @dispatch(str)
    def post(self, url, **kwargs):
        return self.s.post(url, **kwargs)


