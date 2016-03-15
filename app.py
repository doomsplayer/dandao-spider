#!/usr/bin/env python3
"""QZZ Fetcher

The fetcher of qiuzhenzhai(bbs.dandao.net)

Usage:
  qzz.py <command> [(-u<username> -p<password>)] [--url=<url>]

Options:
  --url=<url>             The main site url [default: http://bbs.dandao.net].
  -u <username> --username=<username>   The username.
  -p <password> --password=<password>   The password.
"""
import os
from docopt import docopt
from qzz import Client, Group, Forum, Thread, Post
import logging

def main(username, password, url, arguments):
    logging.basicConfig(level=logging.INFO)
    client = Client(url)
    client.login(username, password)
    Group.update_groups(client)
    Forum.update_forums(client)
    Thread.update_threads(client)
    Post.update_posts(client)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    username = arguments.get("--username", os.environ.get("DANDAO_USERNAME"))
    password = arguments.get("--password", os.environ.get("DANDAO_PASSWORD"))
    url = arguments["--url"]
    main(username, password, url, arguments)
