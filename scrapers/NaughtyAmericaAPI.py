import json
import re
import sys
from argparse import ArgumentParser
from datetime import datetime

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"
ALGOLIA_AGENT = "Algolia for JavaScript (4.5.1); Browser (lite)"
ALGOLIA_API_KEY = "08396b1791d619478a55687b4deb48b4"
ALGOLIA_APP_ID = "I6P9Q9R18E"
SCENE_API_URL = "https://i6p9q9r18e-dsn.algolia.net/1/indexes/nacms_combined_production"
SCENE_IMAGE_URL = "https://images4.naughtycdn.com/cms/nacmscontent/v1/scenes"
SCENE_URL = "https://www.naughtyamerica.com/scene"


def argument_handler():
    parser = ArgumentParser()
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("--scene_url", action="store_true")
    command_group.add_argument("--scene_frag", action="store_true")
    return parser.parse_args()


def debug(*mgs):
    print(*mgs, file=sys.stderr)


def text_to_url(text):
    return re.sub(r"[!:?\"']", "", text).strip().replace(" ", "-").lower()


def scrape_scene_by_url(url):
    scene_json = get_scene_by_url(url=url)
    return scrape_scene(scene_json=scene_json, url=url)


def scrape_scene_by_title(title):
    scene_json = get_scene_by_title(title=title)
    return scrape_scene(scene_json=scene_json)


def get_scene_by_url(url):
    scene_id = re.search(r"-(\d+)", url).group(1)
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(
            (
                f"{SCENE_API_URL}?x-algolia-agent={ALGOLIA_AGENT}&x-algolia-api-key={ALGOLIA_API_KEY}"
                f"&x-algolia-application-id={ALGOLIA_APP_ID}&query={scene_id}"
            ),
            headers=headers,
            timeout=(3, 5),
        )
        assert res.status_code == 200
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    return res.json().get("hits")[0]


def get_scene_by_title(title):
    try:
        scene_name = text_to_url(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = text_to_url(text=title)

    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(
            (
                f"{SCENE_API_URL}?x-algolia-agent={ALGOLIA_AGENT}&x-algolia-api-key={ALGOLIA_API_KEY}"
                f"&x-algolia-application-id={ALGOLIA_APP_ID}&query={scene_name}"
            ),
            headers=headers,
            timeout=(3, 5),
        )
        assert res.status_code == 200
        result = res.json().get("hits")[0]
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request status: {res.reason}")
        debug(f"Request status: {res.url}")
        debug(f"Request status: {res.headers}")
        sys.exit(1)

    if scene_name in result.get("asset_slug"):
        return result

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(scene_json, url=None):
    def generate_url():
        scene_slug = scene_json.get("asset_slug")
        return f"{SCENE_URL}/{scene_slug}"

    def generate_image_url():
        site_acronym = "".join(word[0].lower() for word in scene_json.get("site").split())
        performers_names = "".join(name.split()[0].lower() for name in scene_json.get("working_title").split(", "))
        return f"{SCENE_IMAGE_URL}/{site_acronym}/{performers_names}/scene/horizontal/1279x719c.jpg"

    scene = {}
    scene["title"] = scene_json.get("title")
    scene["url"] = url or generate_url()
    scene["date"] = datetime.utcfromtimestamp(scene_json.get("published_at")).strftime("%Y-%m-%d")
    scene["studio"] = {"name": scene_json.get("site")}
    scene["performers"] = [{"name": actor} for actor in scene_json.get("performers")]
    scene["tags"] = [{"name": tag} for tag in scene_json.get("fantasies")]
    scene["details"] = scene_json.get("synopsis")
    scene["image"] = generate_image_url()

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
