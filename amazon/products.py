import csv

import scrapy
from scrapy_playwright.page import PageMethod
from selenium import webdriver
from scrapy.utils.project import get_project_settings
from ..items import ScraperItem

links = ["https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=1",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=2",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=3",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=4",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=5",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=6",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=7",
         "https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=8",

         ]


class AmazonSpider(scrapy.Spider):
    name = "amazon"

    # start_urls = ["https://www.amazon.de/-/en/gp/bestsellers/toys"]

    def start_requests(self):

        yield scrapy.Request(
            url="https://www.amazon.de/-/en/gp/bestsellers/toys/?ie=UTF8&pg=1",
            meta= dict(
                playwright = True,
                playwright_include_page = True,
                playwright_page_methods =[PageMethod('wait_for_selector', "div[class='a-column a-span12 a-text-center _cDEzb_grid-column_2hIsc']")],
                PLAYWRIGHT_BROWSER_TYPE = "firefox"
            ))

    # def parse_pages(self, response):
    #
    #     products = response.css("div[class='-column a-span12 a-text-center _cDEzb_grid-column_2hIsc']")
    #
    #     for product in products:
    #         url = "https://www.amazon.de" + product.css("div a.a-link-normal::attr(href)").get()
    #         yield scrapy.Request(url, callback=self.parse_product)

    def parse(self, response):
        links = response.xpath('//*[@class="p13n-sc-uncoverable-faceout"]/a[2]')
        for link in links.attrib["href"]:
            yield scrapy.Request(response.urljoin(link), callback = self.parse_pages)

    def parse_pages(self, response):
        see_all = response.css("a[data-hook = see-all-reviews-link-foot]::attr(href)").get()

        yield scrapy.Request(see_all, callback=self.parse_review)

    def parse_review(self, response):
        title = response.css("a.product-link::attr(href)").get()
        eles = response.css("div[class = a-row a-spacing-none]")
        for ele in eles:
            items = ScraperItem()
            items["title"] = title
            items["writer"] = ele.css("span.a-profile-name::text").get()
            items["stars"] = ele.css("i.review-star-rating span::text").get()
            items["short_one"] = ele.css("span.cr-original-review-content::text").get()
            items["long_one"] = ele.css(
                "span[class=a-size-base review-text review-text-content] span.cr-original-review-content::text").get()
            yield items
        next_page = response.css(
            'li[class="a-last"] a::attr(href)').get()
        if next_page is not None:
            yield scrapy.Request(response.urljoin("https://www.amazon.de" + next_page), callback=self.parse_review)
