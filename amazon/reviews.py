import scrapy
from pandas import *
from urllib.parse import urljoin

data = read_csv("8_page.csv")
asin_list = data["asin"].tolist()
#asin_list = ["B01LZYGY8H", "B077PD5W25"]

class AmazonReviewsSpider(scrapy.Spider):
    name="amazon"
    x=0
    p_n = "positive"
    def start_requests(self):
        for asin in asin_list:

            reviews_url_positive = f'https://www.amazon.de/product-reviews/{asin}/ref=cm_cr_arp_d_viewopt_sr?mediaType=text_reviews_only?filterByStar=positive'
            yield scrapy.Request(url=reviews_url_positive, callback=self.parse_reviews, meta={'asin': asin, "retry_count":0})


    def parse_reviews(self, response):
        asin = response.meta['asin']
        retry_count = response.meta["retry_count"]

        ## Get Next Page Url
        #next_page_relative_url = response.css(".a-pagination .a-last>a::attr(href)").get()
        #if next_page_relative_url is not None:
        #    next_page = urljoin('https://www.amazon.com/', next_page_relative_url)
        #    yield scrapy.Request(url=next_page, callback=self.parse_reviews, meta={'asin': asin, "retry_count":0})
        #elif retry_count < 3:
        #    retry_count = retry_count + 1
        #    yield scrapy.Request(url=response.url, callback=self.parse_reviews, dont_filter=True, meta={'asin': asin, "retry_count":0})  

        ## Parse Product Reviews

        if self.x==0:
            self.p_n = "positive"

        review_elements = response.css("#cm_cr-review_list div.review")
        for review_element in review_elements:
            yield {
                    "asin": asin,
                    "text": "".join(review_element.css("span[data-hook=review-body] ::text").getall()).strip(),
                    "title": review_element.css("*[data-hook=review-title]>span::text").get(),
                    "location_and_date": review_element.css("span[data-hook=review-date] ::text").get(),
                    "verified": bool(review_element.css("span[data-hook=avp-badge] ::text").get()),
                    "rating": review_element.css("*[data-hook*=review-star-rating] ::text").re(r"(\d+\.*\d*) out")[0],
                    "positive or negative" : self.p_n
                    }

        

        reviews_url_negative = urljoin("https://www.amazon.de/product-reviews/",f'{asin}/ref=cm_cr_arp_d_viewopt_sr?mediaType=text_reviews_only?filterByStar=critical')
        yield scrapy.Request(url=reviews_url_negative, callback=self.parse_reviews_h, meta={'asin': asin, "retry_count":0})
        

    def parse_reviews_h(self, response):
        asin = response.meta['asin']

        self.x+=1
        if self.x == 1:
            self.p_n = "negative"

        review_elements = response.css("#cm_cr-review_list div.review")
        for review_element in review_elements:
            yield {
                    "asin": asin,
                    "text": review_element.css("span[data-hook=review-body] span::text").get().strip(),
                    "title": review_element.css("*[data-hook=review-title]>span::text").get(),
                    "location_and_date": review_element.css("span[data-hook=review-date] ::text").get(),
                    "verified": bool(review_element.css("span[data-hook=avp-badge] ::text").get()),
                    "rating": review_element.css("*[data-hook*=review-star-rating] ::text").re(r"(\d+\.*\d*) out")[0],
                    "positive or negative" : self.p_n
                    }
        self.x-=1
        
