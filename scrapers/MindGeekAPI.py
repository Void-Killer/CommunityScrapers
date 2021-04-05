import json
import re
import sys
from argparse import ArgumentParser
from datetime import datetime
from urllib.parse import urlparse

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"
SCENE_API_URL = "https://site-api.project1service.com/v2/releases"
ACTOR_API_URL = "https://site-api.project1service.com/v1/actors"
TOKENS_PATH = "__tokens.json"
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


def argument_handler():
    parser = ArgumentParser()
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("--scene_url", action="store_true")
    command_group.add_argument("--scene_frag", action="store_true")
    command_group.add_argument("--actor_url", action="store_true")
    command_group.add_argument("--actor_frag", action="store_true")
    return parser.parse_args()


def debug(*mgs):
    print(*mgs, file=sys.stderr)


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


def text_to_url(text):
    return re.sub(r"[!:?\"']", "", text).replace(" ", "-").lower()


def scrape_scene_by_url(url):
    scene_json = get_scene_by_url(url=url)
    return scrape_scene(scene_json=scene_json, url=url)


def scrape_scene_by_title(title):
    scene_json = get_scene_by_title(title=title)
    return scrape_scene(scene_json=scene_json)


def get_scene_by_url(url):
    scene_id = re.search(r"/(\d+)/*", url).group(1)
    headers = {"Instance": get_token(site=urlparse(url)), "User-Agent": USER_AGENT}

    try:
        res = requests.get(f"{SCENE_API_URL}/{scene_id}", headers=headers, timeout=(3, 5))
        assert res.status_code == 200
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    return res.json().get("result")


def get_scene_by_title(title):
    try:
        scene_name = text_to_url(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
    except AttributeError:
        scene_name = text_to_url(text=title)

    for site in SITE_URLS:
        headers = {"Instance": get_token(site=urlparse(SITE_URLS[site]["scene"])), "User-Agent": USER_AGENT}

        try:
            res = requests.get(
                f"{SCENE_API_URL}?type=scene&limit=1&search={scene_name}", headers=headers, timeout=(3, 5)
            )
            result = res.json().get("result")[0]
        except requests.exceptions.RequestException:
            debug(f"Request status: {res.status_code}")
            debug(f"Request status: {res.reason}")
            debug(f"Request status: {res.url}")
            debug(f"Request status: {res.headers}")
            sys.exit(1)

        if text_to_url(text=result.get("title")) == scene_name:
            result["site"] = site
            return result

    debug("Scene not found")
    debug(text_to_url(text=result.get("title")))
    debug(scene_name)
    sys.exit(1)


def scrape_scene(scene_json, url=None):
    def generate_url():
        site = SITE_URLS[scene.get("site")]["scene"]
        scene_id = scene_json.get("id")
        scene_name = text_to_url(text=scene_json.get("title"))
        return f"{site}/{scene_id}/{scene_name}"

    scene = {}
    scene["title"] = scene_json.get("title")
    scene["url"] = url or generate_url()
    scene["date"] = datetime.strptime(scene_json.get("dateReleased"), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
    scene["studio"] = {"name": scene_json.get("collections")[0].get("name")}
    scene["performers"] = [{"name": x.get("name")} for x in scene_json.get("actors")]
    scene["tags"] = [{"name": x.get("name")} for x in scene_json.get("tags")]
    scene["details"] = scene_json.get("description")
    scene["image"] = scene_json.get("images").get("poster").get("0").get("xx").get("url")

    return scene


def scrape_actor_by_url(url):
    actor_json = get_actor_by_url(url=url)
    return scrape_actor(actor_json=actor_json, url=url)


def scrape_actor_by_name(name):
    actor_json = get_actor_by_name(name=name)
    return scrape_actor(actor_json=actor_json)


def get_actor_by_url(url):
    actor_id = re.search(r"/(\d+)/*", url).group(1)
    headers = {"Instance": get_token(site=urlparse(url)), "User-Agent": USER_AGENT}

    try:
        res = requests.get(f"{ACTOR_API_URL}/{actor_id}", headers=headers, timeout=(3, 5))
        assert res.status_code == 200
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    return res.json().get("result")


def get_actor_by_name(name):
    actor_name = text_to_url(text=name)

    for site in SITE_URLS:
        headers = {"Instance": get_token(site=urlparse(SITE_URLS[site]["actor"])), "User-Agent": USER_AGENT}

        try:
            res = requests.get(f"{ACTOR_API_URL}?limit=1&search={actor_name}", headers=headers, timeout=(3, 5))
            result = res.json().get("result")[0]
        except requests.exceptions.RequestException:
            debug(f"Request status: {res.status_code}")
            debug(f"Request status: {res.reason}")
            debug(f"Request status: {res.url}")
            debug(f"Request status: {res.headers}")
            sys.exit(1)

        if text_to_url(text=result.get("name")) == actor_name:
            result["site"] = site
            return result

    debug("Performer not found")
    debug(text_to_url(text=result.get("name")))
    debug(actor_name)
    sys.exit(1)


def scrape_actor(actor_json, url=None):
    def generate_url():
        site = SITE_URLS[actor_json.get("site")]["actor"]
        actor_id = actor_json.get("id")
        actor_name = text_to_url(text=actor_json.get("name"))
        return f"{site}/{actor_id}/{actor_name}"

    def country_replace():
        country = actor_json.get("birthPlace").split(", ")[-1]
        return "USA" if country.strip() in USA_BIRTHPLACES else country

    def generate_aliases():
        aliases = actor_json.get("aliases")
        try:
            aliases.remove(actor_json.get("name"))
        except ValueError:
            pass
        return ", ".join(aliases)

    actor = {}
    actor["name"] = actor_json.get("name")
    actor["aliases"] = generate_aliases()
    actor["gender"] = actor_json.get("gender")
    actor["birthdate"] = datetime.strptime(actor_json.get("birthday"), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
    actor["country"] = country_replace()
    actor["height"] = str(actor_json.get("height") + 100)
    actor["measurements"] = actor_json.get("measurements")
    actor["fake_tits"] = "Yes" if [x for x in actor_json.get("tags") if x.get("name") == "Enhanced"] else "No"
    actor["url"] = url or generate_url()
    actor["tags"] = [{"name": x.get("name")} for x in actor_json.get("tags")]

    return actor


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
        scraped_json = [scrape_actor_by_name(name=fragment["name"])]
    else:
        sys.exit(1)

    print(json.dumps(scraped_json))


if __name__ == "__main__":
    main()
