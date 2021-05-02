import json
import re
import sys
from datetime import datetime

from utils.resource import Scene
from utils.utilities import USER_AGENT, argument_handler, debug, get_data, text_to_slug

SITE_URLS = {
    "Tushy": "https://www.tushy.com/videos",
    "Deeper": "https://www.vixen.com/videos",
    "Vixen": "https://www.deeper.com/videos",
}


def get_url_redirect(url):
    headers = {"User-Agent": USER_AGENT}
    return get_data(url=url, headers=headers).url


def fetch_page_json(page_html):
    match = re.search(r"__APOLLO_STATE__ = (.+);", page_html).group(1)
    return json.loads(match)


def scrape_scene_by_url(url):
    url = get_url_redirect(url=url)
    raw_data = get_scene_by_url(url=url)
    return scrape_scene(raw_data=raw_data, url=url)


def scrape_scene_by_title(title):
    raw_data = get_scene_by_title(title=title)
    return scrape_scene(raw_data=raw_data)


def get_scene_by_url(url):
    headers = {"User-Agent": USER_AGENT}
    res = get_data(url=url, headers=headers)
    res_json = fetch_page_json(page_html=res.text)
    site_name = re.search(r"\.(.+)\.", res.url).group(1)
    scene_name = res.url.split("/")[-1]

    if f"Video:{site_name}:{scene_name}" in res_json:
        return res_json.get(f"Video:{site_name}:{scene_name}")

    debug("Scene not found")
    sys.exit(1)


def get_scene_by_title(title):
    try:
        scene_name = text_to_slug(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = text_to_slug(text=title)

    for site in SITE_URLS:
        url = f"{SITE_URLS[site]}/{scene_name}"
        headers = {"User-Agent": USER_AGENT}
        res = get_data(url=url, headers=headers, check_rc=False)
        try:
            res_json = fetch_page_json(page_html=res.text)
        except AttributeError:
            continue
        site_name = re.search(r"\.(.+)\.", res.url).group(1)
        scene_name = res.url.split("/")[-1]

        if f"Video:{site_name}:{scene_name}" in res_json:
            res_json = res_json.get(f"Video:{site_name}:{scene_name}")
            res_json["site"] = site
            return res_json

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data, url=None):
    scene = Scene()
    scene.title = raw_data.get("title")
    scene.url = url or f"{SITE_URLS[raw_data.get('site')]}/{raw_data.get('slug')}"
    scene.date = datetime.strptime(raw_data.get("releaseDate"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    scene.studio = {"name": re.search(r"\.(.+)\.", scene.url).group(1).title()}
    scene.performers = [{"name": actor.get("name")} for actor in raw_data.get("models")]
    scene.tags = [{"name": tag.title()} for tag in raw_data.get("tags")]
    scene.details = raw_data.get("description")
    scene.image = raw_data.get("images").get("poster")[-1].get("src")
    return scene.json


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

    print(scraped_json)


if __name__ == "__main__":
    main()
