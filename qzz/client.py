"""
A custom http client with cookie
"""
import requests
from pyquery import PyQuery
from multipledispatch import dispatch

class Client:
    """The qzz specific client"""
    def __init__(self, url="http://bbs.dandao.net"):
        self.url = url.strip("/") + "/"
        self.client = requests.Session()

    def login(self, username, password):
        """Login"""
        resp = self.client.get(self.url)
        document = PyQuery(resp.text)
        form = document.find("form#lsform")
        login_url = self.url + form.attr("action")
        data = {
            "username": username,
            "password": password,
            "handlekey": "ls",
            "quickforward": "yes",
        }
        resp = self.client.post(login_url, data=data)
        query = PyQuery(resp.text)
        resp_username = query.find("strong.vwmy>a").text()
        if resp_username != username:
            alert = query.find("div#messagetext.alert_error>p").text()
            raise RuntimeError("Login failed: {}".format(alert))

    @dispatch(str)
    def get(self, ext, **kwargs):
        """Get the endpoint"""
        return self.client.get(self.url + ext, **kwargs)

