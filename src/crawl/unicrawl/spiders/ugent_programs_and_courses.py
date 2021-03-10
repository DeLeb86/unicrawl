from abc import ABC
from typing import List

import scrapy

from config.settings import YEAR
from config.utils import cleanup
import re

BASE_URL = "https://studiegids.ugent.be/{year}/EN/FACULTY/A/{cycle}/{cycle}.html"


def get_program_version(version_information: str) -> str:
    split_words = re.findall(r"[\w']+", version_information)
    return "".join([word for word in split_words if word.isnumeric()])


def extract_id_from_url_ugent(url: str) -> str:
    split_url = re.findall(r"[\w']+", url)
    return split_url[split_url.index("pdf") - 1]


def extract_url_from_toggle_content(toggle_content: str) -> str:
    url = toggle_content.split(",")[1].replace("'", "")
    return url


def extract_ects(ects_list: List[str]) -> List[str]:
    if "Crdt" in ects_list:
        ects_list.remove("Crdt")

    if "" in ects_list:
        ects_list.remove("")
    return ects_list


def extract_teacher(teacher_list: List[str]) -> List[str]:
    if "Instructor" in teacher_list:
        teacher_list.remove("Instructor")

    if "" in teacher_list:
        teacher_list.remove("")
    return teacher_list


class UgentProgramSpider(scrapy.Spider, ABC):
    name = 'ugent-programs'
    custom_settings = {
        'FEED_URI': f'../../data/crawling-output/ugent_programs_and_courses_{YEAR}.json',
    }

    def start_requests(self):
        for deg in ('BACH', 'MABA'):
            yield scrapy.Request(
                url=BASE_URL.format(year=YEAR, cycle=deg),
                callback=self.parse_main
            )

    def parse_main(self, response):
        faculties_links = response.xpath("//li[a[@target='_top']]/a/@href").getall()
        for link in faculties_links:
            yield response.follow(link, self.parse_programmes)

    def parse_programmes(self, response):
        id = cleanup(response.url.split('/')[-2])
        name = cleanup(response.xpath("//h1")[-1].get())
        cycle = cleanup(name.split(' ')[0])
        url = response.url
        faculty = cleanup(response.xpath("//h2").get())
        year = int(cleanup(response.xpath("//h3").get()).split("-")[-1]) - 1
        version = cleanup(get_program_version(
            response.xpath("//div[@class='menuHeader'][contains(text(), 'Programme')]").get()))

        base_dict = {'id': id,
                     'name': name,
                     'cycle': cycle,
                     'url': url,
                     'faculty': faculty,
                     'year': year,
                     'version(debug)': version}

        link = response.url.split(".html")[0] + version + "(0)/" + id + ".html"
        yield response.follow(link, self.parse_course_list, cb_kwargs={"base_dict": base_dict})

    def parse_course_list(self, response, base_dict):
        parts = [extract_url_from_toggle_content(cleanup(field).split("\n")[0])
                 for field in response.xpath('//a[@onclick[contains(text(), toggleContent)]]/@onclick').getall()]
        yield {**base_dict, **{'parts(debug)': parts}}
        links = [base_dict["url"].split(".html")[0] + base_dict["version(debug)"] + "(0)/" + part
                 for part in parts]

        for link in links:
            yield response.follow(link, self.parse_course_list_final, cb_kwargs={"base_dict": base_dict})

    def parse_course_list_final(self, response, base_dict):
        urls = [cleanup(res) for res in response.xpath("//td[@class='cursus']/a/@href").getall()]
        courses_id = [extract_id_from_url_ugent(url) for url in urls]
        courses_content = ['jojo']*len(courses_id)
        courses_ects = extract_ects([cleanup(res) for res in response.xpath("//td[@class='studiepunten']").getall()])
        courses_teacher = extract_teacher([cleanup(res) for res in response.xpath("//td[@class='lesgever']").getall()])
        final_dict = {**base_dict,
                      **{
                          'url(debug)': response.url[-15:],
                          'courses': courses_id,
                          'courses_ects': courses_ects,
                          'courses_teacher': courses_teacher,
                          'courses_content': courses_content
                      }}
        yield final_dict