import json
from datetime import datetime
from urllib.parse import urlparse


class Resource:
    def to_dict(self):
        return {key.replace("_", ""): val for key, val in self.__dict__.items() if val}

    @property
    def json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def validate_str_val(val, attr_name="", err_msg=None):
        if val and not isinstance(val, str):
            raise ValueError(err_msg if err_msg else f"{attr_name}: got {type(val).__name__} and not str")
        return val

    def validate_range_val(self, val, val_range, attr_name=""):
        if val and val.lower() not in val_range:
            raise ValueError(f"{attr_name}: {val} is not in range {val_range}")
        return val

    def validate_date_val(self, val, attr_name=""):
        self.validate_str_val(val, attr_name=attr_name)
        if val:
            try:
                datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"{attr_name} {val} data format, should be YYYY-MM-DD")
        return val

    def validate_url_val(self, val, attr_name=""):
        self.validate_str_val(val, attr_name=attr_name)
        if not urlparse(val).scheme:
            raise ValueError(f"{attr_name}: {val} is not a valid url")
        return val

    def validate_dict_val(self, val, attr_name=""):
        if not isinstance(val, dict):
            raise ValueError(f"{attr_name}: got {type(val).__name__} and not dict")
        self.validate_str_val(
            val=val.get("name"),
            attr_name=attr_name,
            err_msg=f'{attr_name}: {val} is not a valid dict format {{"name": tag_name (str)}}',
        )
        return val

    def validate_list_dict_val(self, val, attr_name=""):
        if not isinstance(val, list):
            raise ValueError(f"{attr_name}: got {type(val).__name__} and not lst")
        for elem in val:
            self.validate_dict_val(elem, attr_name=attr_name)
        return val


class Performer(Resource):
    """
    Stash performer resource.

    Args:
        name (str)
        aliases (str)
        gender (str): must be one of (case insensitive)
                      male, female, transgender_male, transgender_female, intersex, non_binary
        birthdate (str): format should be YYYY-MM-DD
        deathdate (str): format should be YYYY-MM-DD
        country (str)
        ethnicity (str)
        hair_color (str)
        eye_color (str)
        height (str)
        weight (str)
        measurements (str)
        fake_tits (str): must be one of Yes, No
        tattoos (str)
        piercings (str)
        career_length (str)
        url (str)
        twitter (str)
        instagram (str)
        details (str)
        tags (lst): list of dicts. format [{"name": tag_name (str)}]
        image (str)
    """

    genders_vals = ("male", "female", "transgender_male", "transgender_female", "intersex", "non_binary")
    fake_tits_vals = ("yes", "no")

    def __init__(self):
        super().__init__()
        self._name = None
        self._aliases = None
        self._gender = None
        self._birthdate = None
        self._deathdate = None
        self._country = None
        self._ethnicity = None
        self._hair_color = None
        self._eye_color = None
        self._height = None
        self._weight = None
        self._measurements = None
        self._fake_tits = None
        self._tattoos = None
        self._piercings = None
        self._career_length = None
        self._url = None
        self._twitter = None
        self._instagram = None
        self._details = None
        self._tags = None
        self._image = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = self.validate_str_val(val, attr_name="Name")

    @property
    def aliases(self):
        return self._aliases

    @aliases.setter
    def aliases(self, val):
        self._aliases = self.validate_str_val(val, attr_name="Aliases")

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, val):
        self._gender = self.validate_range_val(val, val_range=self.genders_vals, attr_name="Gender")

    @property
    def birthdate(self):
        return self._birthdate

    @birthdate.setter
    def birthdate(self, val):
        self._birthdate = self.validate_date_val(val, attr_name="Birthdate")

    @property
    def deathdate(self):
        return self._deathdate

    @deathdate.setter
    def deathdate(self, val):
        self._deathdate = self.validate_date_val(val, attr_name="Deathdate")

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, val):
        self._country = self.validate_str_val(val, attr_name="Country")

    @property
    def ethnicity(self):
        return self._ethnicity

    @ethnicity.setter
    def ethnicity(self, val):
        self._ethnicity = self.validate_str_val(val, attr_name="Ethnicity")

    @property
    def hair_color(self):
        return self._hair_color

    @hair_color.setter
    def hair_color(self, val):
        self._hair_color = self.validate_str_val(val, attr_name="HairColor")

    @property
    def eye_color(self):
        return self._eye_color

    @eye_color.setter
    def eye_color(self, val):
        self._eye_color = self.validate_str_val(val, attr_name="EyeColor")

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, val):
        self._height = self.validate_str_val(val, attr_name="Height")

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, val):
        self._weight = self.validate_str_val(val, attr_name="Weight")

    @property
    def measurements(self):
        return self._measurements

    @measurements.setter
    def measurements(self, val):
        self._measurements = self.validate_str_val(val, attr_name="Measurements")

    @property
    def fake_tits(self):
        return self._fake_tits

    @fake_tits.setter
    def fake_tits(self, val):
        self._fake_tits = self.validate_range_val(val, val_range=self.fake_tits_vals, attr_name="FakeTits")

    @property
    def tattoos(self):
        return self._tattoos

    @tattoos.setter
    def tattoos(self, val):
        self._tattoos = self.validate_str_val(val, attr_name="Tattoos")

    @property
    def piercings(self):
        return self._piercings

    @piercings.setter
    def piercings(self, val):
        self._piercings = self.validate_str_val(val, attr_name="Piercings")

    @property
    def career_length(self):
        return self._career_length

    @career_length.setter
    def career_length(self, val):
        self._career_length = self.validate_str_val(val, attr_name="CareerLength")

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, val):
        self._url = self.validate_url_val(val, attr_name="URL")

    @property
    def twitter(self):
        return self._twitter

    @twitter.setter
    def twitter(self, val):
        self._twitter = self.validate_url_val(val, attr_name="Twitter")

    @property
    def instagram(self):
        return self._instagram

    @instagram.setter
    def instagram(self, val):
        self._instagram = self.validate_url_val(val, attr_name="Instagram")

    @property
    def details(self):
        return self._details

    @details.setter
    def details(self, val):
        self._details = self.validate_str_val(val, attr_name="Details")

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, val):
        self._tags = self.validate_list_dict_val(val, attr_name="Tags")

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, val):
        self._image = self.validate_url_val(val, attr_name="Image")


class Scene(Resource):
    """
    Stash scene resource.

    Args:
        title (str)
        url (str)
        date (str): format should be YYYY-MM-DD
        studio (dict): format {"name": studio_name (str)}
        performers (lst): list of dicts. format [{"name": performer_name (str)}]
        movies (lst): list of dicts. format [{"name": movie_name (str)}]
        tags (lst): list of dicts. format [{"name": tag_name (str)}]
        details (str)
        image (str)
    """

    genders_vals = ("male", "female", "transgender_male", "transgender_female", "intersex", "non_binary")
    fake_tits_vals = ("yes", "no")

    def __init__(self):
        super().__init__()
        self._title = None
        self._url = None
        self._date = None
        self._studio = None
        self._performers = None
        self._movies = None
        self._tags = None
        self._details = None
        self._image = None

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, val):
        self._title = self.validate_str_val(val, attr_name="Title")

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, val):
        self._url = self.validate_url_val(val, attr_name="URL")

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, val):
        self._date = self.validate_date_val(val, attr_name="Date")

    @property
    def studio(self):
        return self._studio

    @studio.setter
    def studio(self, val):
        self._studio = self.validate_dict_val(val, attr_name="Studio")

    @property
    def performers(self):
        return self._performers

    @performers.setter
    def performers(self, val):
        self._performers = self.validate_list_dict_val(val, attr_name="Performers")

    @property
    def movies(self):
        return self._movies

    @movies.setter
    def movies(self, val):
        self._movies = self.validate_list_dict_val(val, attr_name="Movies")

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, val):
        self._tags = self.validate_list_dict_val(val, attr_name="Tags")

    @property
    def details(self):
        return self._details

    @details.setter
    def details(self, val):
        self._details = self.validate_str_val(val, attr_name="Details")

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, val):
        self._image = self.validate_url_val(val, attr_name="Image")
