# -*- coding: utf-8 -*-
import scrapy
from cnvd_spider.items import CnvdSpiderItem
import re
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, Spider
import time
import random
from datetime import date
from scrapy import FormRequest
from scrapy.http import Request, HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import ast
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class ExampleSpider(CrawlSpider):
    name = "myspider"
    count = 0
    cookies = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'
    }
    rules = (
        Rule(LinkExtractor(allow=r"www.cnvd.org.cn/flaw/show/*", unique=True),
             callback="parse_news", follow=True),
    )

    allowed_domains = ["www.cnvd.org.cn"]
    # start_urls = ['https://www.cnvd.org.cn/flaw/list.htm?max=20&offset=2050']

    def start_requests(self):
        self.cookies = self.get_cnvd_cookies()
        # ,  meta={'cookiejar': 1}
        yield scrapy.Request(url='https://www.cnvd.org.cn/flaw/list.htm?max=20&offset=2050', headers=self.headers, cookies=self.cookies)

    def _build_request(self, rule, link):
        r = Request(url=link.url, headers=self.headers, cookies=self.cookies,meta={'dont_merge_cookies': True},
                    callback=self._response_downloaded)
        # r.meta['dont_merge_cookies']=True
        r.meta.update(rule=rule, link_text=link.text)
        return r

    def parse_news(self, response):
        response.headers = {}
        item = CnvdSpiderItem()
        time.sleep(random.randint(2, 3))
        self.count += 1
        print(self.count)
        print(self.cookies)
        if (self.count == 3):
            self.cookies = self.get_cnvd_cookies()
            self.count = 0
        # self.cookies = self.get_cnvd_cookies()
        self.get_id(response, item)
        self.get_url(response, item)
        self.get_date(response, item)
        self.get_level(response, item)
        self.get_cve_id(response, item)
        time.sleep(random.randint(1, 2))
        self.get_name(response, item)
        self.get_products(response, item)
        self.get_detail(response, item)
        self.get_types(response, item)
        self.get_refer_url(response, item)
        self.get_method(response, item)
        return item

    def get_cnvd_cookies(self):
        chrome_options = Options()
        # 加上下面两行，解决报错
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get("https://www.cnvd.org.cn/flaw/list.htm?max=20&offset=2550")
        cj = driver.get_cookies()
        cookie = ''
        for c in cj:
            cookie += "'"+c['name'] + "':'" + c['value'] + "',"
        cookie = ast.literal_eval('{'+cookie+'}')
        driver.quit()
        return cookie

    def get_url(self, response, item):
        time.sleep(random.randint(1, 2))
        item['cnvd_url'] = response.url

    def get_name(self, response, item):
        name = response.xpath(
            "//h1/text()").extract()
        # print("\n======="+response.meta['cookiejar']+"================\n")
        if name:
            item['cnvd_name'] = name[0].strip()

    # cnvd_id

    def get_id(self, response, item):
        item["cnvd_id"] = response.xpath(
            "//td[text()='CNVD-ID']/following-sibling::td[1]/text()").extract()
        if item["cnvd_id"]:
            item["cnvd_id"] = "".join(
                [i.strip() for i in item["cnvd_id"]])
        else:
            item["cnvd_id"] = 'Null'

    # 发布日期

    def get_date(self, response, item):
        item["cnvd_date"] = response.xpath(
            "//div[@class='tableDiv']/table[@class='gg_detail']//tr[2]/td[2]/text()").extract()
        if item["cnvd_date"]:
            item["cnvd_date"] = "".join(
                [i.strip() for i in item["cnvd_date"]]).replace('-', '')
            item["cnvd_date"] = self.convertstringtodate(item["cnvd_date"])
        else:
            item["cnvd_date"] = '2000-01-01'.replace('-', '')
            item["cnvd_date"] = self.convertstringtodate(item["cnvd_date"])

    # 危害级别

    def get_level(self, response, item):
        item["cnvd_level"] = response.xpath(
            "//td[text()='危害级别']/following-sibling::td[1]//text()").extract()
        if item["cnvd_level"]:
            item["cnvd_level"] = "".join(
                [i.replace("(", "").replace(")", "").strip() for i in item["cnvd_level"]])
        else:
            item["cnvd_level"] = 'Null'

    # 影响产品

    def get_products(self, response, item):
        item["cnvd_products"] = response.xpath(
            "//table[@class='gg_detail']//tr[td[1]='影响产品']/td[2]/text()").extract()
        if item["cnvd_products"]:
            item["cnvd_products"] = ";".join(
                [i.strip() for i in item["cnvd_products"]])
        else:
            item["cnvd_products"] = 'Null'

    # cve_id

    def get_cve_id(self, response, item):
        item["cnvd_cve_id"] = response.xpath(
            "//td[text()='CVE ID']/following-sibling::td[1]//text()").extract()
        if item["cnvd_cve_id"]:
            item["cnvd_cve_id"] = "".join(
                [i.strip() for i in item["cnvd_cve_id"]])
        else:
            item["cnvd_cve_id"] = 'Null'

    # 漏洞描述

    def get_detail(self, response, item):
        item["cnvd_detail"] = response.xpath(
            "//td[text()='漏洞描述']/following-sibling::td[1]//text()").extract()
        if item["cnvd_detail"]:
            item["cnvd_detail"] = "".join(
                [i.strip() for i in item["cnvd_detail"]]).replace("\u200b", "")
        else:
            item["cnvd_detail"] = 'Null'
    # 漏洞类型

    def get_types(self, response, item):

        types = response.xpath(
            "//table[@class='gg_detail']//tr[td[1]='漏洞类型']/td[2]/text()").extract()

        if types:
            item['cnvd_types'] = types[0].strip()

    # 参考链接
    def get_refer_url(self, response, item):
        item["cnvd_refer_url"] = response.xpath(
            "//td[text()='参考链接']/following-sibling::td[1]/a/@href").extract()
        if item["cnvd_refer_url"]:
            item["cnvd_refer_url"] = item["cnvd_refer_url"][0].replace(
                '\r', '')
        else:
            item["cnvd_refer_url"] = 'Null'

    # 漏洞解决方案

    def get_method(self, response, item):
        item["cnvd_method"] = response.xpath(
            "//td[text()='漏洞解决方案']/following-sibling::td[1]//text()").extract()
        if item["cnvd_method"]:
            item["cnvd_method"] = "".join(
                [i.strip() for i in item["cnvd_method"]])
        else:
            item["cnvd_method"] = 'Null'

    def convertstringtodate(self, stringtime):
        "把字符串类型转换为date类型"
        #  把数据里的时间格式替换成数据库需要的格式。日期格式，便于后期提取数据，
        if stringtime[0:2] == "20":
            year = stringtime[0:4]
            month = stringtime[4:6]
            day = stringtime[6:8]
            if day == "":
                day = "01"
            begintime = date(int(year), int(month), int(day))
            return begintime
        else:
            year = "20" + stringtime[0:2]
            month = stringtime[2:4]
            day = stringtime[4:6]

            begintime = date(int(year), int(month), int(day))
            return begintime
