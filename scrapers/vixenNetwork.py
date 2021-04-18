import json
import re
import sys
from argparse import ArgumentParser
from datetime import datetime

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"
SITE_URLS = {
    "Tushy": "https://www.tushy.com/videos",
    "Deeper": "https://www.vixen.com/videos",
    "Vixen": "https://www.deeper.com/videos",
}


def argument_handler():
    parser = ArgumentParser()
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("--scene_url", action="store_true")
    command_group.add_argument("--scene_frag", action="store_true")
    return parser.parse_args()


def debug(*mgs):
    print(*mgs, file=sys.stderr)


def get_url_redirect(url):
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(url, headers=headers, timeout=(3, 5))
        assert res.status_code == 200
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    return res.url


def fetch_page_json(page_html):
    match = re.search(r"__APOLLO_STATE__ = (.+);", page_html).group(1)
    return json.loads(match)


def text_to_url(text):
    return re.sub(r"[!:?\"']", "", text).strip().replace(" ", "-").lower()


def scrape_scene_by_url(url):
    url = get_url_redirect(url=url)
    scene_json = get_scene_by_url(url=url)
    return scrape_scene(scene_json=scene_json, url=url)


def scrape_scene_by_title(title):
    scene_json = get_scene_by_title(title=title)
    return scrape_scene(scene_json=scene_json)


def get_scene_by_url(url):
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(url, headers=headers, timeout=(3, 5))
        assert res.status_code == 200
        res_json = fetch_page_json(page_html=res.text)
        site_name = re.search(r"\.(.+)\.", res.url).group(1)
        scene_name = res.url.split("/")[-1]
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    if f"Video:{site_name}:{scene_name}" in res_json:
        return res_json.get(f"Video:{site_name}:{scene_name}")

    debug("Scene not found")
    sys.exit(1)


def get_scene_by_title(title):
    try:
        scene_name = text_to_url(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = text_to_url(text=title)
    headers = {"User-Agent": USER_AGENT}

    for site in SITE_URLS:
        try:
            res = requests.get(f"{SITE_URLS[site]}/{scene_name}", headers=headers, timeout=(3, 5))
            res_json = fetch_page_json(page_html=res.text)
            site_name = re.search(r"\.(.+)\.", res.url).group(1)
            scene_name = res.url.split("/")[-1]
        except (requests.exceptions.RequestException, AssertionError):
            debug(f"Request status: {res.status_code}")
            debug(f"Request reason: {res.reason}")
            debug(f"Request url: {res.url}")
            debug(f"Request headers: {res.request.headers}")
            sys.exit(1)

        if f"Video:{site_name}:{scene_name}" in res_json:
            return res_json.get(f"Video:{site_name}:{scene_name}")

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(scene_json, url=None):
    scene = {}
    scene["title"] = scene_json.get("title")
    scene["url"] = url or f"https:{scene_json.get('absoluteUrl')}"
    scene["date"] = datetime.strptime(scene_json.get("releaseDate"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    scene["studio"] = {"name": re.search(r"\.(.+)\.", scene.get("url")).group(1).title()}
    scene["performers"] = [{"name": actor.get("name")} for actor in scene_json.get("models")]
    scene["tags"] = [{"name": tag} for tag in scene_json.get("tags")]
    scene["details"] = scene_json.get("description")
    scene["image"] = scene_json.get("images").get("poster")[-1].get("src")

    return scene


def main():
    args = argument_handler()
    fragment = json.loads(sys.stdin.read())

    if args.scene_url:
        scraped_json = scrape_scene_by_url(url=fragment["url"])
    elif args.scene_frag:
        scraped_json = scrape_scene_by_title(title=fragment["title"])
    else:
        debug("No param passed to script")
        sys.exit(1)

    print(json.dumps(scraped_json))


if __name__ == "__main__":
    main()
