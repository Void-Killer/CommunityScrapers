import re
import sys
from argparse import ArgumentParser

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"


def argument_handler():
    parser = ArgumentParser()
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("--scene_url", action="store_true")
    command_group.add_argument("--scene_frag", action="store_true")
    command_group.add_argument("--actor_url", action="store_true")
    command_group.add_argument("--actor_frag", action="store_true")
    return parser.parse_args()


def debug(mgs):
    print(mgs, file=sys.stderr)


def text_to_slug(text):
    return re.sub(r"[!:?\"']", "", text).strip().replace(" ", "-").lower()


def get_data(url, headers, check_rc=True):
    try:
        res = requests.get(url, headers=headers, timeout=(3, 5))
        assert res.status_code == 200 if check_rc else True
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)
    return res
