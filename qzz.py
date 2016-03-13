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
from models import *
from client import Client



def main(username, password, url, arguments):
    client = Client(username, password, url)
    client.login()
    client.fetch_all_groups()
    client.fetch_all_forums()
    client.fetch_all_threads()
    client.fetch_all_posts()


if __name__ == '__main__':
    arguments = docopt(__doc__)
    username = arguments.get("--username", os.environ.get("DANDAO_USERNAME"))
    password = arguments.get("--password", os.environ.get("DANDAO_PASSWORD"))
    url = arguments["--url"]
    main(username, password, url, arguments)
