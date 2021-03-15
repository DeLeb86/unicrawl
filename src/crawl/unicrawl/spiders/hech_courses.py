# -*- coding: utf-8 -*-
from abc import ABC
from pathlib import Path

import pandas as pd
import scrapy

from config.utils import cleanup
from config.settings import YEAR

BASE_URl = "http://progcours.hech.be/cocoon/cours/{}.html"  # first format is code course, second is year
PROG_DATA_PATH = Path(__file__).parent.absolute().joinpath(
    f'../../../../data/crawling-output/hech_programs_{YEAR}.json')

# TODO: checker langues
LANGUAGES_DICT = {"Langue française": 'fr',
                  "Langue anglaise": 'en'}


class HECHCourseSpider(scrapy.Spider, ABC):
    """
    Course crawler for Haute Ecole Charlemagne
    """

    name = "hech-courses"
    custom_settings = {
        'FEED_URI': Path(__file__).parent.absolute().joinpath(
            f'../../../../data/crawling-output/hech_courses_{YEAR}.json')
    }

    def start_requests(self):

        courses_ids = pd.read_json(open(PROG_DATA_PATH, "r"))["courses"]
        courses_ids_list = sorted(list(set(courses_ids.sum())))

        for course_id in courses_ids_list:
            base_dict = {"id": course_id}
            yield scrapy.Request(BASE_URl.format(course_id), self.parse_main, cb_kwargs={"base_dict": base_dict})

    @staticmethod
    def parse_main(response, base_dict):

        name = response.xpath("////td[@class='LibCours']/text()").get()
        years = response.xpath("//div[@id='TitrePrinc']/text()").get().split(" ")[-1]
        teachers = cleanup(response.xpath("//div[@class='TitreRubCours' and contains(text(), 'prof')]"
                                          "//following::a[1]").getall())
        languages = response.xpath("//div[@class='TitreRubCours' and "
                                   "contains(text(), \"Langue(s) de l'unité d'enseignement\")]"
                                   "//following::td[2]/text()").getall()
        languages = [LANGUAGES_DICT[l] for l in languages]
        # TODO
        content = ""

        cur_dict = {
            'name': name,
            'year': years,
            'teacher': teachers,
            'language': languages,
            'url': response.url,
            'content': content,
        }
        yield {**base_dict, **cur_dict}
