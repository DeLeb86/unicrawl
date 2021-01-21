# -*- coding: utf-8 -*-
from abc import ABC
from pathlib import Path

import pandas as pd

import scrapy

from config.settings import YEAR
from config.utils import cleanup

BASE_URL = "https://uclouvain.be/cours-{}-{}"
PROG_DATA_PATH = Path(f'../../data/crawling-output/ucl_programs_{YEAR}.json')


LANGUAGE_DICT = {"Français": "fr",
                 "Anglais": "en",
                 "Allemand": "de",
                 "Neerlandais": "nl",
                 "Italien": "it",
                 "Espagnol": "es",
                 "Portugais": "pt",
                 "Arabe": 'ar',
                 "Grec": "gr",
                 "Japonais": 'jp',
                 "Russe": "ru"}


class UCLCourseSpider(scrapy.Spider, ABC):
    name = "ucl-courses"
    custom_settings = {
        'FEED_URI': f'../../data/crawling-output/ucl_courses_{YEAR}.json',
    }

    def start_requests(self):

        courses = pd.read_json(open(PROG_DATA_PATH, "r"))["courses"]
        courses_list = sorted(list(set(courses.sum())))

        for course_id in courses_list:
            yield scrapy.Request(url=BASE_URL.format(YEAR, course_id), callback=self.parse_course)

    @staticmethod
    def parse_course(response):

        course_id = cleanup(response.css("span.abbreviation::text").get())
        course_name = cleanup(response.css("h1.header-school::text").get())
        year = cleanup(response.css("span.anacs::text").get())
        campus = cleanup(response.css("span.location::text").get())

        teachers = response.xpath("//div[div[contains(text(),'Enseignants')]]/div/a/text()").getall()
        languages = cleanup(response.xpath("//div[div[contains(@class, 'fa_cell_1') and contains(text(), 'Langue')]]"
                                           "/div[2]/text()").getall())
        languages = [LANGUAGE_DICT[l] for l in languages if l != '']
        
        # content
        sections = ["Thèmes", "Acquis", "Contenu"]
        content = "\n".join([cleanup(response.xpath(f"//div[div[contains(text(),'{section}')]]/div[2]").get())
                             for section in sections])

        data = {
            'id': course_id,
            'name': course_name,
            'year': year,
            'campus': campus,
            'teacher': teachers,
            'language': languages,
            'url': response.url,
            'content': content,
        }
        yield data