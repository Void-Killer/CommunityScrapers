import base64
import json
import re
import sys
from datetime import datetime

from slugify import slugify

from utils.resource import Performer, Scene
from utils.utilities import argument_handler, debug, get_data, xpath_html

SEARCH_URL = "https://www.iafd.com/results.asp?searchtype=comprehensive&searchstring="
SITE_URL = "https://www.iafd.com"
SCENE_URL = "https://www.iafd.com/title.rme/title="
GENDER_MAP = {"f": "Female", "m": "Male"}
XPATHS = {
    "name": "//h1/text()",
    "scene_search": "//a[@class='pop-execute']",
    "scene_date": "//p[text()='Release Date']/following-sibling::p[1]/text()",
    "studio": "//p[text()='Studio']/following-sibling::p//text()",
    "performers": "//div[@class='castbox']/p/a/text()",
    "details": "//div[@id='synopsis']/div[@class='padded-panel']//text()",
    "actor_search": "//a[contains(@href,'person.rme')]",
    "aliases": "//div[p[text()='\nPerformer\nAKA']]//div[@class='biodata']/text()",
    "gender": "//input[@name='Gender']/@value",
    "bithdate": "//p[text()='Birthday']/following-sibling::p/a/text()",
    "death_date": "//p[text()='Date of Death']/following-sibling::p/text()",
    "country": "//p[text()='Birthplace']/following-sibling::p/text()",
    "ethnicity": "//p[text()='Ethnicity']/following-sibling::p/text()",
    "hair_color": "//p[text()='Hair Colors']/following-sibling::p/text()",
    "height": "//p[text()='Height']/following-sibling::p/text()",
    "weight": "//p[text()='Weight']/following-sibling::p/text()",
    "measurements": "//p[text()='Measurements']/following-sibling::p/text()",
    "tatoos": "//p[text()='Tattoos']/following-sibling::p/text()",
    "piercings": "//p[text()='Piercings']/following-sibling::p/text()",
    "career_length": "//p[text()='Years Active']/following-sibling::p/text()",
    "actor_url": "//*[contains(@href,'person.rme')]/@href",
    "twitter": "//p[text()='Website']/following-sibling::p/a/@href",
    "instagram": "//p[@class='biodata']/a[contains(text(),'instagram')]/@href",
    "actor_image": "//div[@id='headshot']/img",
}


def scrape_scene_by_url(url):
    raw_data = get_scene_by_url(url=url)
    return scrape_scene(raw_data=raw_data, url=url)


def scrape_scene_by_title(title):
    raw_data = get_scene_by_title(title=title)
    return scrape_scene(raw_data=raw_data)


def get_scene_by_url(url):
    try:
        return get_data(url=url).text
    except Exception as err:
        debug(err)
        debug("Scene not found")
        sys.exit(1)


def get_scene_by_title(title):
    try:
        scene_name = re.search(r"\((.+?)\)\s\(\d*-", title).group(1).lower()
    except AttributeError:
        scene_name = title.lower()

    try:
        html = get_data(url=f"{SEARCH_URL}{scene_name}").text
        matches = xpath_html(html, xpath=XPATHS["scene_search"], get_first=False)
        for match in matches:
            if scene_name in match.text.lower():
                return get_data(url=f"{SITE_URL}{match.values()[1]}").text
    except Exception:
        pass

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data, url=None):
    def generate_url():
        year = scene.date.split("-")[0]
        return f"{SCENE_URL}{slugify(scene.title, separator='+')}/year={year}/{slugify(scene.title)}"

    scene = Scene()
    scene.title = re.sub(r"\(\d*\)", "", xpath_html(html=raw_data, xpath=XPATHS["name"])).strip()
    scene.date = datetime.strptime(
        xpath_html(html=raw_data, xpath=XPATHS["scene_date"]).strip(),
        "%b %d, %Y",
    ).strftime("%Y-%m-%d")
    scene.studio = {"name": xpath_html(html=raw_data, xpath=XPATHS["studio"])}
    scene.performers = [
        {"name": actor} for actor in xpath_html(html=raw_data, xpath=XPATHS["performers"], get_first=False)
    ]
    scene.details = xpath_html(html=raw_data, xpath=XPATHS["details"])
    scene.url = url or generate_url()
    return scene.json


def scrape_actor_by_url(url):
    raw_data = get_actor_by_url(url=url)
    return scrape_actor(raw_data=raw_data, url=url)


def scrape_actor_by_name(name):
    raw_data = get_actor_by_name(name=name)
    return scrape_actor(raw_data=raw_data)


def get_actor_by_url(url):
    try:
        return get_data(url=url).text
    except Exception as err:
        debug(err)
        debug("Performer not found")
        sys.exit(1)


def get_actor_by_name(name):
    actors = []
    try:
        html = get_data(url=f"{SEARCH_URL}{name}").text
        matches = xpath_html(html, xpath=XPATHS["actor_search"], get_first=False)
        for match in matches:
            if match.text and name in match.text:
                actors.append(get_data(url=f"{SITE_URL}{match.values()[0]}").text)
    except Exception as err:
        debug(err)
        debug("Performer not found")
        sys.exit(1)

    if actors:
        return actors

    debug("Performer not found")
    sys.exit(1)


def scrape_actor(raw_data, url=None):
    def parse_date(date_type):
        try:
            xpath = XPATHS["bithdate"] if date_type == "birth" else XPATHS["death_date"]
            return datetime.strptime(
                re.search(r"(\S+\s+\d+,\s+\d+)", xpath_html(html=raw_data, xpath=xpath)).group(1), "%B %d, %Y"
            ).strftime("%Y-%m-%d")
        except Exception:
            return

    def image_decode():
        image = get_data(url=xpath_html(html=raw_data, xpath=XPATHS["actor_image"]).values()[-1]).content
        return f"data:image/jpeg;base64,{base64.b64encode(image).decode('utf-8')}"

    if type(raw_data) is list:
        actors = []
        for performer in raw_data:
            actor = Performer()
            actor.name = xpath_html(html=performer, xpath=XPATHS["name"]).strip()
            actor.url = f"{SITE_URL}{xpath_html(html=performer, xpath=XPATHS['actor_url'])}"
            actors.append(actor.to_dict())
        return json.dumps(actors)
    else:
        actor = Performer()
        actor.name = xpath_html(html=raw_data, xpath=XPATHS["name"]).strip()
        actor.aliases = xpath_html(html=raw_data, xpath=XPATHS["aliases"])
        actor.gender = GENDER_MAP[xpath_html(html=raw_data, xpath=XPATHS["gender"])]
        actor.birthdate = parse_date(date_type="birth")
        actor.death_date = parse_date(date_type="death")
        try:
            actor.country = xpath_html(html=raw_data, xpath=XPATHS["country"]).split(",")[-1].strip()
        except Exception:
            pass
        actor.ethnicity = xpath_html(html=raw_data, xpath=XPATHS["ethnicity"])
        actor.hair_color = xpath_html(html=raw_data, xpath=XPATHS["hair_color"])
        try:
            actor.height = re.search(r"\((\d*) cm\)", xpath_html(html=raw_data, xpath=XPATHS["height"])).group(1)
        except Exception:
            pass
        try:
            actor.weight = re.search(r"\((\d*) kg\)", xpath_html(html=raw_data, xpath=XPATHS["weight"])).group(1)
        except Exception:
            pass
        actor.measurements = xpath_html(html=raw_data, xpath=XPATHS["measurements"])
        actor.tattoos = xpath_html(html=raw_data, xpath=XPATHS["tatoos"])
        actor.piercings = xpath_html(html=raw_data, xpath=XPATHS["piercings"])
        try:
            actor.career_length = re.search(
                r"(\S*)\s\(", xpath_html(html=raw_data, xpath=XPATHS["career_length"])
            ).group(1)
        except Exception:
            pass
        actor.url = url or f"{SITE_URL}{xpath_html(html=raw_data, xpath=XPATHS['actor_url'])}"
        actor.twitter = xpath_html(html=raw_data, xpath=XPATHS["twitter"])
        actor.instagram = xpath_html(html=raw_data, xpath=XPATHS["instagram"])
        actor.image = image_decode()
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
