import json
import re
import sys
from argparse import ArgumentParser

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"
SCENE_API_URL = "https://metadataapi.net/api/scenes"
ACTOR_API_URL = "https://metadataapi.net/api/performers"
ACTOR_URL = "https://metadataapi.net/performers"
API_KEY = "Z0jkfUe0xWCDAElL5HEVTFO8i6OohAu7MzGSQeoU"


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


def text_to_url(text):
    return re.sub(r"[!:?\"']", "", text).strip().replace(" ", "-").lower()


def scrape_scene_by_url(url):
    scene_json = get_scene_by_url(url=url)
    return scrape_scene(scene_json=scene_json)


def scrape_scene_by_title(title):
    scene_json = get_scene_by_title(title=title)
    return scrape_scene(scene_json=scene_json)


def get_scene_by_url(url):
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}
    scene_name = url.split("/")[-1]

    try:
        res = requests.get(f"{SCENE_API_URL}/{scene_name}", headers=headers, timeout=(3, 5))
        assert res.status_code == 200
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    return res.json().get("data")


def get_scene_by_title(title):
    try:
        parsed_site = re.search(r"\[(.*?)\]", title).group(1)
        site_name = text_to_url(text=" ".join(re.findall("([A-Z][^A-Z]*)", parsed_site)))
        scene_name = text_to_url(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
        search_name = f"{site_name}-{scene_name}"
    except AttributeError:
        scene_name = text_to_url(text=title)

    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}

    try:
        res = requests.get(f"{SCENE_API_URL}?parse={search_name}&limit=1", headers=headers, timeout=(3, 5))
        assert res.status_code == 200
        debug(res.json())
        result = res.json().get("data")[0]
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request status: {res.reason}")
        debug(f"Request status: {res.url}")
        debug(f"Request status: {res.headers}")
        sys.exit(1)

    debug(search_name)
    debug(text_to_url(text=result.get("slug")))
    if text_to_url(text=result.get("slug")) == search_name:
        return result

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(scene_json):
    scene = {}
    scene["title"] = scene_json.get("title")
    scene["url"] = scene_json.get("url")
    scene["date"] = scene_json.get("date")
    scene["studio"] = {"name": scene_json.get("site").get("name")}
    scene["performers"] = [{"name": actor.get("name")} for actor in scene_json.get("performers")]
    scene["tags"] = [{"name": tag.get("name")} for tag in scene_json.get("tags")]
    scene["details"] = scene_json.get("description")
    scene["image"] = scene_json.get("image")

    return scene


def scrape_actor_by_url(url):
    actor_json = get_actor_by_url(url=url)
    return scrape_actor(actor_json=actor_json, url=url)


def scrape_actor_by_name(name):
    actor_json = get_actor_by_name(name=name)
    return scrape_actor(actor_json=actor_json)


def get_actor_by_url(url):
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}
    actor_name = url.split("/")[-1]

    try:
        res = requests.get(f"{ACTOR_API_URL}/{actor_name}", headers=headers, timeout=(3, 5))
        assert res.status_code == 200
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request reason: {res.reason}")
        debug(f"Request url: {res.url}")
        debug(f"Request headers: {res.request.headers}")
        sys.exit(1)

    return res.json().get("data")


def get_actor_by_name(name):
    actors = []
    actor_name = text_to_url(text=name)
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}

    try:
        res = requests.get(f"{ACTOR_API_URL}?q={actor_name}", headers=headers, timeout=(3, 5))
        assert res.status_code == 200
        result = res.json().get("data")
    except (requests.exceptions.RequestException, AssertionError):
        debug(f"Request status: {res.status_code}")
        debug(f"Request status: {res.reason}")
        debug(f"Request status: {res.url}")
        debug(f"Request status: {res.headers}")
        sys.exit(1)

    for match in result:
        if actor_name in match.get("slug"):
            if not [actor for actor in actors if match.get("id") == actor.get("id")]:
                actors.append(match)

    if actors:
        return actors
    else:
        debug("Performer not found")
        debug(actor_name)
        sys.exit(1)


def scrape_actor(actor_json, url=None):
    def country_replace(country):
        if country:
            return country.split(", ")[-1].replace("United Kingdom", "UK").replace("United States", "USA")

    def height_weight_extract(value):
        if value:
            return re.search("([0-9]*)", value).group(1)

    def details_extract(details):
        if details:
            return details.replace("BIOGRAPHY:", "").replace("CLOSE BIO", "").strip()

    actors = []
    if type(actor_json) is list:
        for model in actor_json:
            actor = {}
            actor["name"] = model.get("name")
            actor["gender"] = model.get("extras").get("gender")
            actor["birthdate"] = model.get("extras").get("birthday")
            actor["country"] = country_replace(country=model.get("extras").get("birthplace"))
            actor["ethnicity"] = model.get("extras").get("ethnicity")
            actor["hair_color"] = model.get("extras").get("hair_colour")
            actor["height"] = height_weight_extract(value=model.get("extras").get("height"))
            actor["weight"] = height_weight_extract(value=model.get("extras").get("weight"))
            actor["measurements"] = model.get("extras").get("measurements")
            actor["tattoos"] = model.get("extras").get("tattoos")
            actor["piercings"] = model.get("extras").get("piercings")
            actor["url"] = url or f"{ACTOR_URL}/{model.get('slug')}"
            actor["details"] = details_extract(details=model.get("bio"))
            actor["image"] = model.get("image")
            actors.append(actor)
    else:
        actor = {}
        actor["name"] = actor_json.get("name")
        actor["aliases"] = ", ".join(actor_json.get("aliases"))
        actor["gender"] = actor_json.get("extras").get("gender")
        actor["birthdate"] = actor_json.get("extras").get("birthday")
        actor["country"] = country_replace(country=actor_json.get("extras").get("birthplace"))
        actor["ethnicity"] = actor_json.get("extras").get("ethnicity")
        actor["hair_color"] = actor_json.get("extras").get("hair_colour")
        actor["height"] = height_weight_extract(value=actor_json.get("extras").get("height"))
        actor["weight"] = height_weight_extract(value=actor_json.get("extras").get("weight"))
        actor["measurements"] = actor_json.get("extras").get("measurements")
        actor["tattoos"] = actor_json.get("extras").get("tattoos")
        actor["piercings"] = actor_json.get("extras").get("piercings")
        actor["url"] = url or f"{ACTOR_URL}/{actor_json.get('slug')}"
        actor["details"] = details_extract(details=actor_json.get("bio"))
        actor["image"] = actor_json.get("image")

    return actors or actor


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

    print(json.dumps(scraped_json))


if __name__ == "__main__":
    main()
