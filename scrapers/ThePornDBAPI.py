import json
import re
import sys

from utils.resource import Performer, Scene
from utils.utilities import USER_AGENT, argument_handler, debug, get_data, text_to_slug

SCENE_API_URL = "https://metadataapi.net/api/scenes"
ACTOR_API_URL = "https://metadataapi.net/api/performers"
ACTOR_URL = "https://metadataapi.net/performers"
API_KEY = "Z0jkfUe0xWCDAElL5HEVTFO8i6OohAu7MzGSQeoU"


def scrape_scene_by_url(url):
    raw_data = get_scene_by_url(url=url)
    return scrape_scene(raw_data=raw_data)


def scrape_scene_by_title(title):
    raw_data = get_scene_by_title(title=title)
    return scrape_scene(raw_data=raw_data)


def get_scene_by_url(url):
    scene_name = url.split("/")[-1]
    request_url = f"{SCENE_API_URL}/{scene_name}"
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}
    return get_data(url=request_url, headers=headers).json().get("data")


def get_scene_by_title(title):
    try:
        parsed_site = re.search(r"\[(.*?)\]", title).group(1)
        site_name = text_to_slug(text=" ".join(re.findall("([A-Z][^A-Z]*)", parsed_site)))
        scene_name = text_to_slug(text=re.search(r"\((.+?)\)\s\(\d*-", title).group(1))
        search_name = f"{site_name}-{scene_name}"
    except AttributeError:
        search_name = text_to_slug(text=title)
    url = f"{SCENE_API_URL}?parse={search_name}&limit=1"
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}
    res = get_data(url=url, headers=headers).json().get("data")[0]

    if search_name in res.get("slug"):
        return res

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data):
    scene = Scene()
    scene.title = raw_data.get("title")
    scene.url = raw_data.get("url").split("?")[0].replace("site-ma.brazzers.com/scene", "www.brazzers.com/video")
    scene.date = raw_data.get("date")
    scene.studio = {"name": raw_data.get("site").get("name")}
    scene.performers = [{"name": actor.get("name")} for actor in raw_data.get("performers")]
    scene.tags = [{"name": tag.get("name").title()} for tag in raw_data.get("tags", {})]
    scene.details = raw_data.get("description")
    scene.image = raw_data.get("image")
    return scene.json


def scrape_actor_by_url(url):
    raw_data = get_actor_by_url(url=url)
    return scrape_actor(raw_data=raw_data, url=url)


def scrape_actor_by_name(name):
    raw_data = get_actor_by_name(name=name)
    return scrape_actor(raw_data=raw_data)


def get_actor_by_url(url):
    actor_name = url.split("/")[-1]
    request_url = f"{ACTOR_API_URL}/{actor_name}"
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}
    return get_data(url=request_url, headers=headers).json().get("data")


def get_actor_by_name(name):
    actors = []
    actor_name = text_to_slug(text=name)
    url = f"{ACTOR_API_URL}?q={actor_name}"
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {API_KEY}"}
    res = get_data(url=url, headers=headers).json().get("data")

    for match in res:
        if actor_name in match.get("slug"):
            if not [actor for actor in actors if match.get("id") == actor.get("id")]:
                actors.append(match)

    if actors:
        return actors

    debug("Performer not found")
    sys.exit(1)


def scrape_actor(raw_data, url=None):
    def country_replace(country):
        if country:
            return country.split(", ")[-1].replace("United Kingdom", "UK").replace("United States", "USA")

    def height_weight_extract(value):
        if value:
            return re.search("([0-9]*)", value).group(1)

    def details_extract(details):
        if details:
            return details.replace("BIOGRAPHY:", "").replace("CLOSE BIO", "").strip()

    if type(raw_data) is list:
        actors = []
        for performer in raw_data:
            actor = Performer()
            actor.name = performer.get("name")
            actor.url = f"{ACTOR_URL}/{performer.get('slug')}"
            actors.append(actor.to_dict())
        return json.dumps(actors)
    else:
        actor = Performer()
        actor.name = raw_data.get("name")
        actor.aliases = ", ".join(raw_data.get("aliases", []))
        actor.gender = raw_data.get("extras").get("gender")
        actor.birthdate = raw_data.get("extras").get("birthday")
        actor.country = country_replace(country=raw_data.get("extras").get("birthplace"))
        actor.ethnicity = raw_data.get("extras").get("ethnicity")
        actor.hair_color = raw_data.get("extras").get("hair_colour")
        actor.height = height_weight_extract(value=raw_data.get("extras").get("height"))
        actor.weight = height_weight_extract(value=raw_data.get("extras").get("weight"))
        actor.measurements = raw_data.get("extras").get("measurements")
        actor.tattoos = raw_data.get("extras").get("tattoos")
        actor.piercings = raw_data.get("extras").get("piercings")
        actor.url = url
        actor.details = details_extract(details=raw_data.get("bio"))
        actor.image = raw_data.get("image")
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
