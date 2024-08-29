from selenium import webdriver
from selenium.webdriver.remote.webdriver import (
    WebDriver,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from amazoncaptcha import AmazonCaptcha

import re
import time
import datetime
import random


class Item:
    def __init__(
        self,
        category_asin: int,
        category_name: str,
        product_asin: str,
        title: str,
        review_num: int,
        rating: float,
        description: str,
        color: str,
        price: float,
        last_month_sold: int,
        status: str = None,
        created_date: datetime.datetime = datetime.datetime.now(),
    ):
        self.category_asin: int = category_asin
        self.category_name: str = category_name
        self.product_asin: str = product_asin
        self.title: str = title
        self.review_num: int = review_num
        self.rating: float = rating
        self.description: str = description
        self.color: str = color
        self.price: float = price
        self.status: str = status
        self.last_month_sold: int = last_month_sold
        self.created_date: datetime.datetime = created_date

    def __str__(self):
        return (
            f"CATEGORY_ASIN: {self.category_asin}\n"
            f"CATEGORY_NAME: {self.category_name}\n"
            f"PRODUCT_ASIN: {self.product_asin}\n"
            f"TITLE: {self.title}\n"
            f"REVIEW_NUM: {self.review_num}\n"
            f"RATING: {self.rating}\n"
            f"DESCRIPTION: {self.description}\n"
            f"COLOR: {self.color}\n"
            f"PRICE: {self.price}\n"
            f"STATUS: {self.status}\n"
            f"LAST_MONTH_SOLD: {self.last_month_sold}\n"
            f"CREATED_DATE: {self.created_date}"
        )


class Category:
    def __init__(self, url: str, category_asin: str, category_name: str):
        self.url: str = url
        self.category_asin: int = category_asin
        self.category_name: str = category_name
        self.product_list_asins: list[tuple[str, bool]] = []
        self.product_list: list[Item] = []
        self.sub_category_urls: list[tuple[str, bool]] = []
        self.sub_category_list: list[Category] = []


class Extactor:
    def __init__(self, zipcode=92104):
        self.driver_options = Options()

        self.driver = webdriver.Chrome(options=self.driver_options)

        self.wait = WebDriverWait(self.driver, 10)
        self.zipcode = zipcode

        self.driver.get("https://www.amazon.com/")
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

        self.sleep_interval = 2

        # INITIALIZE
        time.sleep(self.sleep_interval)

        self.check_and_bypass_amazon_captcha()
        self.choose_location_to_delivery_to(zipcode)

    def check_and_bypass_amazon_captcha(self):
        time.sleep(self.sleep_interval)

        text = self.soup_try_to_find("h4")
        if text:
            captcha_image_link = self.soup_try_to_find("img", {}, "src")
            captcha = AmazonCaptcha.fromlink(captcha_image_link)
            solution = captcha.solve()
            self.driver.find_element(By.ID, "captchacharacters").send_keys(solution)
            self.driver.find_element(By.CLASS_NAME, "a-button-text").click()

        time.sleep(self.sleep_interval)

    def choose_location_to_delivery_to(self, zipcode: int = 92104):
        if self.wait:
            self.wait.until(
                EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-action='GLUXPostalInputAction']")
                )
            ).send_keys(zipcode)
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[aria-labelledby='GLUXZipUpdate-announce']")
                )
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".a-popover-footer #GLUXConfirmClose")
                )
            ).click()

        time.sleep(self.sleep_interval)

    def soup_try_to_find(
        self, name: str, attribute: dict = {}, get_value_from_attribute: str = None
    ):
        try:
            if get_value_from_attribute:
                return self.soup.find(name, attribute).get(get_value_from_attribute)
            else:
                return self.soup.find(name, attribute).text.strip()
        except:
            return None

    def extract_amazon_product_from_url(
        self,
        product_url: str,
        zipcode: int = 92104,
        category_asin: int = None,
        category_name: str = None,
    ):
        """
        Extract Amazon products from URL.

        Args:
            product_url (str): Product url

        Returns:
            Item | None: Item objects if successful
        """

        if not product_url or len(product_url) == 0:
            return None

        self.driver.get(product_url)

        self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))

        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # CATEGORY_ASIN (get from parameter)

        # CATEGORY_NAME (get from parameter)

        # PRODUCT_ASIN
        product_asin = self.soup_try_to_find("input", {"id": "ASIN"}, "value")

        # TITLE
        title = self.soup_try_to_find("span", {"id": "productTitle"})

        # REVIEWS
        review_num = self.soup_try_to_find("span", {"id": "acrCustomerReviewText"})
        if review_num:
            review_num = int(re.match(r"\d+", review_num).group())

        # RATING
        rating = self.soup_try_to_find(
            "span",
            {"data-hook": "rating-out-of-text"},
        )
        if rating:
            rating = float(re.search(r"\d+(\.\d+)?", rating).group())

        # DESCRIPTION
        ul_element = self.soup.find(
            "ul", class_="a-unordered-list a-vertical a-spacing-mini"
        )

        # Find all <li> elements within the <ul>
        li_elements = ul_element.find_all("li", class_="a-spacing-mini")
        description = []
        for li in li_elements:
            description.append(li.text.strip())

        # COLOR
        color = self.soup_try_to_find("span", {"class": "selection"})

        # PRICE
        price = float(
            re.findall(
                r"\d+\.\d+|\d+",
                self.soup_try_to_find("span", {"class": "aok-offscreen"}),
            )[0]
        )

        # STATUS
        status = self.soup_try_to_find(
            "span", {"class": "a-size-medium a-color-success"}
        )

        # LAST MONTH SOLD
        last_month_sold = self.soup_try_to_find(
            "span", {"id": "social-proofing-faceout-title-tk_bought"}
        )
        match = re.search(r"\d+(?:[KkMm])?", last_month_sold)
        if match:
            last_month_sold = match.group()
            if "K" in match.group().upper():
                last_month_sold = int(last_month_sold[:-1])
                last_month_sold *= 1000
            elif "M" in match.group().upper():
                last_month_sold = int(last_month_sold[:-1])
                last_month_sold *= 1000000
            else:
                last_month_sold = int(last_month_sold)

        # CREATED_DATE
        created_date = datetime.datetime.now()

        return Item(
            category_asin=category_asin,
            category_name=category_name,
            product_asin=product_asin,
            title=title,
            review_num=review_num,
            rating=rating,
            description=description,
            color=color,
            price=price,
            status=status,
            last_month_sold=last_month_sold,
            created_date=created_date,
        )


def main():
    URL = "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/141-3078590-5074935?pd_rd_w=MABN3&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=0Y582SYJA52XPQ46D08Z&pd_rd_wg=WBZ2b&pd_rd_r=d16f64de-fd58-48a9-b10c-27becea887e2&pd_rd_i=B0CX18TFQD&th=1"

    extractor = Extactor()
    new_product = extractor.extract_amazon_product_from_url(URL)
    print(new_product)


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.5f} seconds")
