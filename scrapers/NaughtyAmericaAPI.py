import json
import re
import sys
from datetime import datetime

from utils.resource import Scene
from utils.utilities import USER_AGENT, argument_handler, debug, get_data, text_to_slug

SCENE_API_URL = "https://i6p9q9r18e-dsn.algolia.net/1/indexes/nacms_combined_production"
SCENE_IMAGE_URL = "https://images4.naughtycdn.com/cms/nacmscontent/v1/scenes"
SCENE_URL = "https://www.naughtyamerica.com/scene"
ALGOLIA_AGENT = "Algolia for JavaScript (4.5.1); Browser (lite)"
ALGOLIA_API_KEY = "08396b1791d619478a55687b4deb48b4"
ALGOLIA_APP_ID = "I6P9Q9R18E"
ALGOLIA_REQUEST_URL = (
    f"{SCENE_API_URL}?x-algolia-agent={ALGOLIA_AGENT}&x-algolia-api-key={ALGOLIA_API_KEY}"
    f"&x-algolia-application-id={ALGOLIA_APP_ID}"
)


def scrape_scene_by_url(url):
    raw_data = get_scene_by_url(url=url)
    return scrape_scene(raw_data=raw_data, url=url)


def scrape_scene_by_title(title):
    raw_data = get_scene_by_title(title=title)
    return scrape_scene(raw_data=raw_data)


def get_scene_by_url(url):
    scene_id = re.search(r"-(\d+)", url).group(1)
    request_url = f"{ALGOLIA_REQUEST_URL}&query={scene_id}"
    headers = {"User-Agent": USER_AGENT}
    return get_data(url=request_url, headers=headers).json().get("hits")[0]


def get_scene_by_title(title):
    try:
        scene_name = text_to_slug(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = text_to_slug(text=title)
    url = f"{ALGOLIA_REQUEST_URL}&query={scene_name}"
    headers = {"User-Agent": USER_AGENT}
    res = get_data(url=url, headers=headers).json().get("hits")[0]

    if scene_name in res.get("asset_slug"):
        return res

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data, url=None):
    def generate_url():
        scene_slug = raw_data.get("asset_slug")
        return f"{SCENE_URL}/{scene_slug}"

    def generate_image_url():
        site_acronym = "".join(word[0].lower() for word in raw_data.get("site").split())
        performers_names = "".join(name.split()[0].lower() for name in raw_data.get("working_title").split(", "))
        return f"{SCENE_IMAGE_URL}/{site_acronym}/{performers_names}/scene/horizontal/1279x719c.jpg"

    scene = Scene()
    scene.title = raw_data.get("title")
    scene.url = url or generate_url()
    scene.date = datetime.utcfromtimestamp(raw_data.get("published_at")).strftime("%Y-%m-%d")
    scene.studio = {"name": raw_data.get("site")}
    scene.performers = [{"name": actor} for actor in raw_data.get("performers")]
    scene.tags = [{"name": tag.capitalize()} for tag in raw_data.get("fantasies")]
    scene.details = raw_data.get("synopsis")
    scene.image = generate_image_url()
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
