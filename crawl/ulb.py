# -*- coding: utf-8 -*-

import scrapy
import argparse

import scrapy
from scrapy.crawler import CrawlerProcess
from w3lib.html import remove_tags


#<div class="champ contenu_formation toolbox">

class ULBSpider(scrapy.Spider):
    name = "ulb"

    def start_requests(self):
        base_url = 'https://www.ulb.be/fr/programme/lien-vers-catalogue-des-programmes'
        yield scrapy.Request(url=base_url, callback=self.parse)

    def parse(self, response):
        for href in response.css("a[class='item-title__element_title']::attr(href)"):
            yield response.follow(href, self.parse_prog)

    def parse_prog(self, response):
        program = response.url + '#programme'
        for href in response.css("li a[href^='" + program + "-']::attr(href)"):
            yield response.follow(href, self.parse_course)

    def parse_course(self, response):
        data = {
            'type':         self._cleanup(response.xpath("//div//strong[contains(text(), 'Type de titre')]/following::p").get()),
            'duration':     self._cleanup(response.xpath("//div//strong[contains(text(), 'de la formation')]/following::p").get()),
            'language':     self._cleanup(response.xpath("//div//strong[contains(text(), 'Campus')]/following::p").get()),
            'category':     self._cleanup(response.xpath("//div//strong[contains(text(), '(s) et universit')]/following::a[1]").get()),
            'faculty':      self._cleanup(response.xpath("//div//strong[contains(text(), '(s) et universit')]/following::a[2]").get()),
            'url':          response.url
        }
        yield data

    def _cleanup(self, data):
        if data is None:
            return ""
        elif isinstance(data, list):
            result = list()
            for e in data:
                result.append(self._cleanup(e))
            return result
        else:
            return remove_tags(data).strip()


def main(output):
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'FEED_FORMAT': 'json',
        'FEED_URI': output
    })

    process.crawl(ULBSpider)
    process.start() # the script will block here until the crawling is finished
    print('All done.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl the UCL courses catalog.')
    parser.add_argument("--output", default="output.json", type=str, help="Output file")
    args = parser.parse_args()
    main(args.output)