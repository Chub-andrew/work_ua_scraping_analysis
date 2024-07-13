from scrapy.http import Response
import scrapy
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


class WorkuaSpider(scrapy.Spider):
    name = "workua"
    allowed_domains = ["work.ua"]
    start_urls = ["https://www.work.ua/jobs-python/"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = webdriver.Chrome()

    def close(self, reason):
        self.driver.close()

    def parse(self, response: Response, **kwargs):
        """
        Parse the list of job postings and follow the links to detailed pages.
        """
        for tech in response.css(".card-hover"):
            yield response.follow(
                tech.css('h2 > a::attr(href)').get(),
                callback=self.parse_detail_page
            )

        next_button = response.css(".pagination > li")[-1].css("a::attr(href)").get()
        if next_button:
            next_button = response.urljoin(next_button)
            yield scrapy.Request(next_button, callback=self.parse)

    def parse_detail_page(self, response: Response):
        """
        Parse the detailed job page.
        """
        self.driver.get(response.url)
        name_element = self.get_job_name()
        technology_list = self.get_technologies_block()


        yield {
            "name": name_element,
            "technologies": technology_list,

        }

    def get_job_name(self):
        name_element = self.driver.find_element(By.CSS_SELECTOR, "ol > li:last-child").text
        return name_element

    def get_technologies_block(self):

        try:
            self.check_all_technologies_button()
        except NoSuchElementException:
            return None
        finally:
            technologies_block = self.driver.find_element(By.CLASS_NAME, "toggle-block")
            technologies = technologies_block.find_elements(By.CLASS_NAME, "label-skill")

            technology_list = []

            for technology in technologies:
                technology_list.append(technology.text)

            return technology_list

    def check_all_technologies_button(self):
        all_tech_button = self.driver.find_element(
            By.CSS_SELECTOR, "a.block-relative.link-icon.nowrap.w-100.text-center.js-toggle-btn"
        )
        all_tech_button.click()