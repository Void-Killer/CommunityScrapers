import json
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

from slugify import slugify

from utils.resource import Movie, Performer, Scene
from utils.utilities import argument_handler, debug, get_data

SCENE_API_URL = "https://tsmkfa364q-dsn.algolia.net/1/indexes/all_scenes"
ACTOR_API_URL = "https://tsmkfa364q-dsn.algolia.net/1/indexes/all_actors"
MOVIE_API_URL = "https://tsmkfa364q-dsn.algolia.net/1/indexes/all_movies"
SCENE_IMAGE_URL = "https://transform.gammacdn.com/movies"
ACTOR_IMAGE_URL = "https://transform.gammacdn.com/actors"
TOKENS_PATH = "utils\\tokens.json"
SITE_URLS = {
    "21 Sextury": {"addr": "https://www.21sextury.com", "paths": {"scene": "en/video", "actor": "en/pornstar"}},
    "21 Sextreme": {"addr": "https://www.21sextreme.com", "paths": {"scene": "en/video", "actor": "en/pornstar"}},
    "21 Bonus": {"addr": "https://www.21sextury.com", "paths": {"scene": "en/video", "actor": "en/pornstar"}},
    "Burning Angel": {"addr": "https://www.burningangel.com", "paths": {"scene": "en/video", "actor": "en/pornstar"}},
    "Evilangel": {
        "addr": "https://www.evilangel.com",
        "paths": {"scene": "en/video", "actor": "en/pornstar", "movie": "en/movies"},
    },
    "Rocco Siffredi": {
        "addr": "https://www.roccosiffredi.com",
        "paths": {"scene": "en/video", "actor": "en/pornstar", "movie": "en/dvds"},
    },
    "Fantasy Massage": {
        "addr": "https://www.fantasymassage.com",
        "paths": {"scene": "en/video", "actor": "en/pornstar"},
    },
}
ALGOLIA_AGENT = "Algolia for JavaScript (3.35.1); Browser (lite)"
ALGOLIA_APP_ID = "TSMKFA364Q"
ALGOLIA_REQUEST_SCENE_URL = f"{SCENE_API_URL}?x-algolia-agent={ALGOLIA_AGENT}&x-algolia-application-id={ALGOLIA_APP_ID}"
ALGOLIA_REQUEST_ACTOR_URL = f"{ACTOR_API_URL}?x-algolia-agent={ALGOLIA_AGENT}&x-algolia-application-id={ALGOLIA_APP_ID}"
ALGOLIA_REQUEST_MOVIE_URL = f"{MOVIE_API_URL}?x-algolia-agent={ALGOLIA_AGENT}&x-algolia-application-id={ALGOLIA_APP_ID}"


def get_token(url):
    def generate_token():
        res = get_data(f"{url.scheme}://{url.netloc}")
        api_json = json.loads(re.search(r"window.env.*= ({.+});", res.text).group(1))
        token = api_json.get("api").get("algolia").get("apiKey")

        tokens[url.netloc] = {"token": token, "date": datetime.today().strftime("%Y-%m-%d:%H")}
        with open(TOKENS_PATH, "w+", encoding="utf-8") as token_file:
            json.dump(tokens, token_file, ensure_ascii=False, indent=4)

    tokens = {}
    try:
        tokens = json.load(open(TOKENS_PATH))
        token = tokens[url.netloc]
    except (FileNotFoundError, json.decoder.JSONDecodeError, KeyError):
        generate_token()
        token = tokens[url.netloc]

    if token["date"] != datetime.today().strftime("%Y-%m-%d:%H"):
        generate_token()
        token = tokens[url.netloc]

    return token["token"]


def scrape_scene_by_url(url):
    raw_data = get_scene_by_url(url=url)
    return scrape_scene(raw_data=raw_data, url=url)


def scrape_scene_by_title(title):
    raw_data = get_scene_by_title(title=title)
    return scrape_scene(raw_data=raw_data)


def get_scene_by_url(url):
    url = urlparse(url.replace("www.fantasymassage.com", "www.21sextury.com"))
    scene_id = re.search(r"\/(\d+)", url.path).group(1)
    request_url = f"{ALGOLIA_REQUEST_SCENE_URL}&x-algolia-api-key={get_token(url=url)}&query={scene_id}"
    headers = {"Origin": url.netloc}

    try:
        return get_data(url=request_url, headers=headers).json().get("hits")[0]
    except Exception as err:
        debug(err)
        debug("Scene not found")
        sys.exit(1)


def get_scene_by_title(title):
    try:
        scene_name = slugify(re.search(r"\((.+?)\)\s\(\d*-", title).group(1)).replace("gaping", "")
    except AttributeError:
        scene_name = slugify(title).replace("gaping", "")

    for _, url in SITE_URLS.items():
        request_url = (
            f"{ALGOLIA_REQUEST_SCENE_URL}&x-algolia-api-key={get_token(url=urlparse(url['addr']))}&query={scene_name}"
        )
        headers = {"Origin": url["addr"]}
        try:
            res = get_data(url=request_url, headers=headers).json().get("hits")[0]
        except Exception:
            continue
        if scene_name in slugify(res.get("title")):
            return res

    debug("Scene not found")
    sys.exit(1)


def scrape_scene(raw_data, url=None):
    def generate_url():
        site = SITE_URLS[raw_data.get("network_name")]["addr"]
        path = SITE_URLS[raw_data.get("network_name")]["paths"]["scene"]
        scene_slug = raw_data.get("url_title")
        scene_id = raw_data.get("clip_id")
        return f"{site}/{path}/{scene_slug}/{scene_id}"

    def generate_image_url():
        if datetime.strptime(scene.date, "%Y-%m-%d") >= datetime.strptime("2010", "%Y"):
            image_url = raw_data.get("pictures").get("960x540") or raw_data.get("pictures").get("960x544")
        else:
            image_url = raw_data.get("pictures").get("300x225")
        return f"{SCENE_IMAGE_URL}{image_url}?g"

    scene = Scene()
    scene.title = raw_data.get("title")
    scene.url = url or generate_url()
    scene.date = raw_data.get("release_date")
    scene.studio = {"name": raw_data.get("studio_name").title()}
    scene.performers = [{"name": actor.get("name")} for actor in raw_data.get("actors")]
    if SITE_URLS[raw_data.get("network_name")]["paths"].get("movie"):
        scene.movies = [{"name": raw_data.get("movie_title")}]
    scene.tags = [{"name": tag.get("name").title()} for tag in raw_data.get("categories") if tag.get("name")]
    scene.details = raw_data.get("description")
    scene.image = generate_image_url()
    return scene.json


def scrape_actor_by_url(url):
    raw_data = get_actor_by_url(url=url)
    return scrape_actor(raw_data=raw_data, url=url)


def scrape_actor_by_name(name):
    raw_data = get_actor_by_name(name=name)
    return scrape_actor(raw_data=raw_data)


def get_actor_by_url(url):
    url = urlparse(url.replace("www.fantasymassage.com", "www.21sextury.com"))
    actor_name = url.geturl().split("/")[-2]
    request_url = f"{ALGOLIA_REQUEST_ACTOR_URL}&x-algolia-api-key={get_token(url=url)}&query={actor_name}"
    headers = {"Origin": url.netloc}

    try:
        return get_data(url=request_url, headers=headers).json().get("hits")[0]
    except Exception as err:
        debug(err)
        debug("Performer not found")
        sys.exit(1)


def get_actor_by_name(name):
    actor_name = slugify(name)
    actors = []

    for _, url in SITE_URLS.items():
        url = url["addr"].replace("www.fantasymassage.com", "www.21sextury.com")
        request_url = f"{ALGOLIA_REQUEST_ACTOR_URL}&x-algolia-api-key={get_token(url=urlparse(url))}&query={actor_name}"
        headers = {"Origin": url}
        res = get_data(url=request_url, headers=headers).json().get("hits")
        for match in res:
            if actor_name in slugify(match.get("name")) and match.get("network_name") in SITE_URLS:
                if not [actor for actor in actors if match.get("actor_id") == actor.get("actor_id")]:
                    actors.append(match)

    if actors:
        return actors

    debug("Performer not found")
    sys.exit(1)


def scrape_actor(raw_data, url=None):
    def generate_url(actor):
        site = SITE_URLS[actor.get("network_name")]["addr"]
        path = SITE_URLS[actor.get("network_name")]["paths"]["actor"]
        actor_id = actor.get("actor_id")
        actor_name = slugify(actor.get("name"))
        return f"{site}/{path}/{actor_name}/{actor_id}"

    def generate_image_url():
        image_url = raw_data.get("pictures").get("500x750")
        return f"{ACTOR_IMAGE_URL}{image_url}?g"

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
        actor.aliases = raw_data.get("attributes").get("alternate_names")
        actor.gender = raw_data.get("gender")
        actor.ethnicity = raw_data.get("attributes").get("ethnicity")
        actor.hair_color = raw_data.get("attributes").get("hair_color")
        actor.eye_color = raw_data.get("attributes").get("eye_color")
        actor.url = url or generate_url(actor=raw_data)
        actor.details = raw_data.get("description")
        actor.tags = [{"name": tag.get("name").title()} for tag in raw_data.get("categories") if tag.get("name")]
        actor.image = generate_image_url()
        return actor.json


def scrape_movie_by_url(url):
    raw_data = get_movie_by_url(url=url)
    return scrape_movie(raw_data=raw_data, url=url)


def get_movie_by_url(url):
    url = urlparse(url)
    movie_name = url.geturl().split("/")[-2]
    request_url = f"{ALGOLIA_REQUEST_MOVIE_URL}&x-algolia-api-key={get_token(url=url)}&query={movie_name}&hitsPerPage=9"
    headers = {"Origin": url.netloc}
    try:
        res = get_data(url=request_url, headers=headers).json().get("hits")
        for match in res:
            if slugify(movie_name).lower() == match.get("url_title").lower():
                return match
    except Exception as err:
        debug(err)
        debug("Movie not found")
        sys.exit(1)


def scrape_movie(raw_data, url):
    def generate_image_url(side):
        image_path = raw_data.get("cover_path")
        return f"{SCENE_IMAGE_URL}{image_path}_{side}_400x625.jpg?enlarge=true"

    movie = Movie()
    movie.name = raw_data.get("title")
    movie.duration = raw_data.get("total_length")
    movie.date = raw_data.get("last_modified")
    movie.studio = {"name": raw_data.get("sitename_pretty").title()}
    movie.director = raw_data.get("directors")[0].get("name")
    movie.url = url
    movie.synopsis = raw_data.get("description")
    movie.front_image = generate_image_url(side="front")
    movie.back_image = generate_image_url(side="back")
    return movie.json


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
    elif args.movie_url:
        scraped_json = scrape_movie_by_url(url=fragment["url"])
    else:
        debug("No param passed to script")
        sys.exit(1)

    print(scraped_json)


if __name__ == "__main__":
    main()
