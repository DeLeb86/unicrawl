# -*- coding: utf-8 -*-
from abc import ABC
from pathlib import Path

import scrapy

from settings import YEAR, CRAWLING_OUTPUT_FOLDER

BASE_URL = "http://progcours.hech.be/cocoon/fac/fac{}"
DEPARTMENTS_CODES = {"A": "Département Agronomique",
                     "E": "Département Economique",
                     "M": "Département Paramédicale",
                     "P": "Département Pédagogique"}


class HECHProgramSpider(scrapy.Spider, ABC):
    """
    Program crawler for Haute Ecole Charlemagne
    """

    name = "hech-programs"
    custom_settings = {
        'FEED_URI': Path(__file__).parent.absolute().joinpath(
            f'../../../../{CRAWLING_OUTPUT_FOLDER}hech_programs_{YEAR}.json').as_uri()
    }

    def start_requests(self):
        for code in DEPARTMENTS_CODES.keys():
            base_dict = {"faculty": DEPARTMENTS_CODES[code]}
            yield scrapy.Request(BASE_URL.format(code), self.parse_main, cb_kwargs={'base_dict': base_dict})

    def parse_main(self, response, base_dict):
        # Get list of faculties
        programs_names = response.xpath(f"//a[@class='LienProg']/text()").getall()
        programs_links = response.xpath(f"//a[@class='LienProg']/@href").getall()
        programs_codes = [link.split("/")[-1].split("_")[0] for link in programs_links]
        programs_cycles = [name.split(" ")[0].lower() for name in programs_names]

        for name, code, link, cycle in zip(programs_names, programs_codes, programs_links, programs_cycles):
            cur_dict = {'name': name,
                        'id': code,
                        'cycle': cycle}
            yield response.follow(link, self.parse_program, cb_kwargs={'base_dict': {**base_dict, **cur_dict}})

    @staticmethod
    def parse_program(reponse, base_dict):

        ects = reponse.xpath("//td[contains(@class, 'ContColG')]/text()").getall()
        ects = [e for e in ects if e != '\xa0']
        # TODO: check if there are UEs -> probably the reason there are '\xao'
        courses_ids = reponse.xpath("//nobr/text()").getall()

        cur_dict = {"ects": ects,
                    "courses": courses_ids  # ,
                    # "ectsnb": len(ects),
                    # "coursesnb": len(courses_ids)
                    }

        yield {**base_dict, **cur_dict}
