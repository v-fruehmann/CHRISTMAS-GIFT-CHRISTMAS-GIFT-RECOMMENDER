import scrapy
from pandas import *

data = read_csv("data.csv")
asin_list = data["asin"].tolist()


# asin_list = ["B01LZYGY8H", "B077PD5W25"]

class ProductSpider(scrapy.Spider):
    name = "product"

    def start_requests(self):
        for asin in asin_list:
            url = f'https://www.amazon.de/dp/{asin}'
            yield scrapy.Request(url=url, callback=self.parse_product, meta={'asin': asin})

    def parse_product(self, response):
        asin = response.meta['asin']
        yield {
            "asin": asin,
            "Age_range": response.css(
                'tr[class="a-spacing-small po-age_range_description"] td[class="a-span9"] span[class="a-size-base"]::text').get(),
            "About_this_item": ";".join(response.css(
                'div[class="a-section a-spacing-medium a-spacing-top-small"] ul li span::text').getall()).strip()
        }
