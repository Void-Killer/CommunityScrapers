import json
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

from slugify import slugify

from utils.resource import Performer, Scene
from utils.utilities import argument_handler, debug, get_data

SCENE_API_URL = "https://site-api.project1service.com/v2/releases"
ACTOR_API_URL = "https://site-api.project1service.com/v1/actors"
TOKENS_PATH = "utils\\tokens.json"
SITE_URLS = {
    "brazzers": {"addr": "https://www.brazzers.com", "paths": {"scene": "video", "actor": "pornstar"}},
    "realitykings": {"addr": "https://www.realitykings.com", "paths": {"scene": "scene", "actor": "model"}},
    "mofos": {"addr": "https://www.mofos.com", "paths": {"scene": "scene", "actor": "model"}},
    "babes": {"addr": "https://www.babes.com", "paths": {"scene": "scene", "actor": "model"}},
    "digitalplayground": {
        "addr": "https://www.digitalplayground.com",
        "paths": {"scene": "scene", "actor": "modelprofile"},
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
        res = get_data(f"{site.scheme}://{site.netloc}")
        token = res.cookies.get_dict().get("instance_token")

        tokens[site.netloc] = {"token": token, "date": datetime.today().strftime("%Y-%m-%d")}
        with open(TOKENS_PATH, "w+", encoding="utf-8") as f:
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
    scene_id = re.search(r"/(\d+)/*", url).group(1)
    request_url = f"{SCENE_API_URL}/{scene_id}"
    headers = {"Instance": get_token(site=urlparse(url))}

    try:
        return get_data(url=request_url, headers=headers).json().get("result")
    except Exception as err:
        debug(err)
        debug("Scene not found")
        sys.exit(1)


def get_scene_by_title(title):
    try:
        scene_name = slugify(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = slugify(text=title)

    for _, url in SITE_URLS.items():
        request_url = f"{SCENE_API_URL}?type=scene&limit=1&search={scene_name}"
        headers = {"Instance": get_token(site=urlparse(url["addr"]))}
        try:
            res = get_data(url=request_url, headers=headers).json().get("result")[0]
        except Exception:
            continue
        if scene_name in slugify(text=res.get("title")):
            return res

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data, url=None):
    def generate_url():
        site = SITE_URLS[raw_data.get("brand")]["addr"]
        path = SITE_URLS[raw_data.get("brand")]["paths"]["scene"]
        scene_id = raw_data.get("id")
        scene_name = slugify(text=raw_data.get("title"))
        return f"{site}/{path}/{scene_id}/{scene_name}"

    scene = Scene()
    scene.title = raw_data.get("title")
    scene.url = url or generate_url()
    scene.date = datetime.strptime(raw_data.get("dateReleased"), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
    scene.studio = {"name": raw_data.get("collections")[0].get("name")}
    scene.performers = [{"name": actor.get("name")} for actor in raw_data.get("actors")]
    scene.tags = [{"name": tag.get("name").title()} for tag in raw_data.get("tags")]
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
    headers = {"Instance": get_token(site=urlparse(url))}
    try:
        return get_data(url=request_url, headers=headers).json().get("result")
    except Exception as err:
        debug(err)
        debug("Scene not found")
        sys.exit(1)


def get_actor_by_name(name):
    actor_name = slugify(text=name)

    actors = []
    for site, url in SITE_URLS.items():
        request_url = f"{ACTOR_API_URL}?limit=8&search={actor_name}"
        headers = {"Instance": get_token(site=urlparse(url["addr"]))}
        try:
            res = get_data(url=request_url, headers=headers).json().get("result")
        except Exception:
            continue
        for match in res:
            if actor_name in slugify(text=match.get("name")):
                if not [actor for actor in actors if match.get("id") == actor.get("id")]:
                    match["site"] = site
                    actors.append(match)

    if actors:
        return actors

    debug("Performer not found")
    sys.exit(1)


def scrape_actor(raw_data, url=None):
    def generate_url(actor):
        site = SITE_URLS[actor["site"]]["addr"]
        path = SITE_URLS[actor["site"]]["paths"]["actor"]
        actor_id = actor.get("id")
        actor_name = slugify(text=actor.get("name"))
        return f"{site}/{path}/{actor_id}/{actor_name}"

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

    if type(raw_data) is list:
        actors = []
        for performer in raw_data:
            actor = Performer()
            actor.name = performer.get("name")
            actor.url = generate_url(actor=performer)
            actors.append(actor.to_dict())
        return json.dumps(actors)
    else:
        actor = Performer()
        actor.name = raw_data.get("name")
        actor.aliases = generate_aliases(actor=raw_data)
        actor.gender = raw_data.get("gender")
        actor.birthdate = datetime.strptime(raw_data.get("birthday"), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
        actor.country = country_replace(actor=raw_data)
        actor.height = str(raw_data.get("height") + 100)
        actor.weight = str(round(raw_data.get("weight") / 2.205))
        actor.measurements = raw_data.get("measurements")
        actor.fake_tits = "Yes" if [tag for tag in raw_data.get("tags") if tag.get("name") == "Enhanced"] else "No"
        actor.url = url or generate_url(actor=raw_data)
        actor.details = raw_data.get("bio")
        actor.tags = [{"name": tag.get("name").title()} for tag in raw_data.get("tags")]
        actor.image = raw_data.get("images").get("card_main_rect").get("0").get("xl").get("url")
        return actor.json


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
