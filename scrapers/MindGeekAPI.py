import json
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

import requests

from utils.resource import Performer, Scene
from utils.utilities import USER_AGENT, argument_handler, debug, get_data, text_to_slug

SCENE_API_URL = "https://site-api.project1service.com/v2/releases"
ACTOR_API_URL = "https://site-api.project1service.com/v1/actors"
TOKENS_PATH = "utils\\tokens.json"
SITE_URLS = {
    "Brazzers": {"scene": "https://www.brazzers.com/video", "actor": "https://www.brazzers.com/pornstar"},
    "Reality Kings": {"scene": "https://www.realitykings.com/scene", "actor": "https://www.realitykings.com/model"},
    "Mofos": {"scene": "https://www.mofos.com/scene", "actor": "https://www.mofos.com/model"},
    "Babes": {"scene": "https://www.babes.com/scene", "actor": "https://www.babes.com/model"},
    "Digital Playground": {
        "scene": "https://www.digitalplayground.com/scene",
        "actor": "https://www.digitalplayground.com/modelprofile",
    },
}
USA_BIRTHPLACES = (
    "AK, AL, AR, AZ, CA, CO, CT, DC, DE, FL, GA, HI, IA, ID, IL, IN, KS, KY, LA, MA, MD, ME, MI, MN, MO, MS, MT, NC, "
    "ND, NE, NH, NJ, NM, NV, NY, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VA, VT, WA, WI, WV, WY, Alabama, Alaska, "
    "Arizona, Arkansas, California, Colorado, Connecticut, Delaware, Florida, Georgia, Hawaii, Idaho, Illinois, "
    "Indiana, Iowa, Kansas, Kentucky, Louisiana, Maine, Maryland, Massachusetts, Michigan, Minnesota, Mississippi, "
    "Missouri, Montana, Nebraska, Nevada, New Hampshire, New Jersey, New Mexico, New York, North Carolina, "
    "North Dakota, Ohio, Oklahoma, Oregon, Pennsylvania, Rhode Island, South Carolina, South Dakota, Tennessee, "
    "Texas, Utah, Vermont, Virginia, Washington, West Virginia, Wisconsin, Wyoming"
)


def get_token(site):
    def generate_token():
        res = requests.get(f"{site.scheme}://{site.netloc}", timeout=(3, 5))
        token = res.cookies.get_dict().get("instance_token")

        tokens[site.netloc] = {"token": token, "date": datetime.today().strftime("%Y-%m-%d")}
        with open(TOKENS_PATH, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False, indent=4)

    tokens = {}
    try:
        tokens = json.load(open(TOKENS_PATH))
        token = tokens[site.netloc]
    except (FileNotFoundError, json.decoder.JSONDecodeError, KeyError):
        generate_token()
        token = tokens[site.netloc]

    if token["date"] != datetime.today().strftime("%Y-%m-%d"):
        generate_token()
        token = tokens[site.netloc]

    return token["token"]


def scrape_scene_by_url(url):
    raw_data = get_scene_by_url(url=url)
    return scrape_scene(raw_data=raw_data, url=url)


def scrape_scene_by_title(title):
    raw_data = get_scene_by_title(title=title)
    return scrape_scene(raw_data=raw_data)


def get_scene_by_url(url):
    debug(url)
    scene_id = re.search(r"/(\d+)/*", url).group(1)
    request_url = f"{SCENE_API_URL}/{scene_id}"
    headers = {"Instance": get_token(site=urlparse(url)), "User-Agent": USER_AGENT}
    return get_data(url=request_url, headers=headers).json().get("result")


def get_scene_by_title(title):
    try:
        scene_name = text_to_slug(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = text_to_slug(text=title)

    for site in SITE_URLS:
        url = f"{SCENE_API_URL}?type=scene&limit=1&search={scene_name}"
        headers = {"Instance": get_token(site=urlparse(SITE_URLS[site]["scene"])), "User-Agent": USER_AGENT}
        res = get_data(url=url, headers=headers).json().get("result")[0]
        if text_to_slug(text=res.get("title")) == scene_name:
            res["site"] = site
            return res

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data, url=None):
    def generate_url():
        site = SITE_URLS[raw_data.get("site")]["scene"]
        scene_id = raw_data.get("id")
        scene_name = text_to_slug(text=raw_data.get("title"))
        return f"{site}/{scene_id}/{scene_name}"

    scene = Scene()
    scene.title = raw_data.get("title")
    scene.url = url or generate_url()
    scene.date = datetime.strptime(raw_data.get("dateReleased"), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
    scene.studio = {"name": raw_data.get("collections")[0].get("name")}
    scene.performers = [{"name": actor.get("name")} for actor in raw_data.get("actors")]
    scene.tags = [{"name": tag.get("name").capitalize()} for tag in raw_data.get("tags")]
    scene.details = raw_data.get("description")
    scene.image = raw_data.get("images").get("poster").get("0").get("xx").get("url")
    return scene.json


def scrape_actor_by_url(url):
    raw_data = get_actor_by_url(url=url)
    return scrape_actor(raw_data=raw_data, url=url)


def scrape_actor_by_name(name):
    raw_data = get_actor_by_name(name=name)
    return scrape_actor(raw_data=raw_data)


def get_actor_by_url(url):
    actor_id = re.search(r"/(\d+)/*", url).group(1)
    request_url = f"{ACTOR_API_URL}/{actor_id}"
    headers = {"Instance": get_token(site=urlparse(url)), "User-Agent": USER_AGENT}
    return get_data(url=request_url, headers=headers).json().get("result")


def get_actor_by_name(name):
    actor_name = text_to_slug(text=name)

    actors = []
    for site in SITE_URLS:
        url = f"{ACTOR_API_URL}?limit=8&search={actor_name}"
        headers = {"Instance": get_token(site=urlparse(SITE_URLS[site]["actor"])), "User-Agent": USER_AGENT}
        res = get_data(url=url, headers=headers).json().get("result")
        for match in res:
            if actor_name in text_to_slug(text=match.get("name")):
                if not [actor for actor in actors if match.get("id") == actor.get("id")]:
                    match["site"] = site
                    actors.append(match)

    if actors:
        return actors

    debug("Performer not found")
    sys.exit(1)


def scrape_actor(raw_data, url=None):
    def generate_url(actor):
        site = SITE_URLS[actor.get("site")]["actor"]
        actor_id = actor.get("id")
        actor_name = text_to_slug(text=actor.get("name"))
        return f"{site}/{actor_id}/{actor_name}"

    def country_replace(actor):
        country = actor.get("birthPlace").split(", ")[-1].replace("United Kingdom", "UK")
        return "USA" if country.strip() in USA_BIRTHPLACES else country

    def generate_aliases(actor):
        aliases = actor.get("aliases")
        try:
            aliases.remove(actor.get("name"))
        except ValueError:
            pass
        return ", ".join(aliases)

    def parse_actor(performer):
        actor = Performer()
        actor.name = performer.get("name")
        actor.aliases = generate_aliases(actor=performer)
        actor.gender = performer.get("gender")
        actor.birthdate = datetime.strptime(performer.get("birthday"), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
        actor.country = country_replace(actor=performer)
        actor.height = str(performer.get("height") + 100)
        actor.weight = str(round(performer.get("weight") / 2.205))
        actor.measurements = performer.get("measurements")
        actor.fake_tits = "Yes" if [tag for tag in performer.get("tags") if tag.get("name") == "Enhanced"] else "No"
        actor.url = url or generate_url(actor=performer)
        actor.details = performer.get("bio")
        actor.tags = [{"name": tag.get("name").capitalize()} for tag in performer.get("tags")]
        actor.image = performer.get("images").get("card_main_rect").get("0").get("xl").get("url")
        return actor

    if type(raw_data) is list:
        actors = []
        for performer in raw_data:
            actors.append(parse_actor(performer=performer).to_dict())
        return json.dumps(actors)
    else:
        return parse_actor(performer=raw_data).json


def main():
    args = argument_handler()
    fragment = json.loads(sys.stdin.read())

    if args.scene_url:
        scraped_json = scrape_scene_by_url(url=fragment["url"])
    elif args.scene_frag:
        scraped_json = scrape_scene_by_title(title=fragment["title"])
    elif args.actor_url:
        scraped_json = scrape_actor_by_url(url=fragment["url"])
    elif args.actor_frag:
        scraped_json = scrape_actor_by_name(name=fragment["name"])
    else:
        debug("No param passed to script")
        sys.exit(1)

    print(scraped_json)


if __name__ == "__main__":
    main()
