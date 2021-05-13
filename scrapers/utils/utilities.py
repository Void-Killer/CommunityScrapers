import sys
from argparse import ArgumentParser

import cloudscraper
from lxml import etree


def argument_handler():
    parser = ArgumentParser()
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("--scene_url", action="store_true")
    command_group.add_argument("--scene_frag", action="store_true")
    command_group.add_argument("--actor_url", action="store_true")
    command_group.add_argument("--actor_frag", action="store_true")
    command_group.add_argument("--movie_url", action="store_true")
    return parser.parse_args()


def debug(mgs):
    print(mgs, file=sys.stderr)


def xpath_html(html, xpath, get_first=True):
    tree = etree.HTML(html)
    if get_first:
        try:
            match = tree.xpath(f"{xpath}")[0]
            assert "No data" not in match
        except Exception:
            return None
        return match
    else:
        return tree.xpath(f"{xpath}")


def get_data(url, headers=None, check_rc=True):
    scraper = cloudscraper.create_scraper()
    try:
        res = scraper.get(url, headers=headers, timeout=(3, 5))
        assert res.status_code == 200 if check_rc else True
    except AssertionError:
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)
    return res
