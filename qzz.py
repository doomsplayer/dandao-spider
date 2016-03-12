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
import models
from client import Client



def main(username, password, url):
    client = Client(username, password, url)
    client.login()
    #resp = client.get("http://bbs.dandao.net/forum.php?mod=viewthread&tid=3993")
    #print(resp.text)



if __name__ == '__main__':
    arguments = docopt(__doc__)
    username = arguments.get("--username", os.environ.get("DANDAO_USERNAME"))
    password = arguments.get("--password", os.environ.get("DANDAO_PASSWORD"))
    url = arguments["--url"]
    main(username, password, url)
