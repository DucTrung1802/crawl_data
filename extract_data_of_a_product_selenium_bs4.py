from selenium import webdriver
from selenium.webdriver.remote.webdriver import (
    WebDriver,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import re
import time
import datetime
import random


class Item:
    def __init__(
        self,
        id: str,
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
        self.id = id
        self.category_asin = category_asin
        self.category_name = category_name
        self.product_asin = product_asin
        self.title = title
        self.review_num = review_num
        self.rating = rating
        self.description = description
        self.color = color
        self.price = price
        self.status = status
        self.last_month_sold = last_month_sold
        self.created_date = created_date


class Extactor:
    def __init__(self, zipcode=92104):
        self.driver_options = Options()

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/92.0.902.84 Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        ]

        self.driver = webdriver.Chrome(options=self.driver_options)
        self.get_random_header()

        self.wait = WebDriverWait(self.driver, 10)
        self.soup = None
        self.zipcode = zipcode

    def get_random_header(self):
        random.seed()

        self.driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": self.user_agents[random.randint(0, len(self.user_agents))]},
        )

        self.driver.execute_script("return navigator.userAgent;")

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

    def soup_try_to_find(
        self, name: str, attribute: dict, get_value_from_attribute: str = None
    ):
        try:
            if get_value_from_attribute:
                return self.soup.find(name, attribute).get("value")
            else:
                return self.soup.find(name, attribute).text.strip()
        except:
            return None

    def extract_amazon_product_data_from_url(
        self,
        url_list: list[str],
        zipcode: int = 92104,
        category_asin: int = None,
        category_name: str = None,
    ):
        """
        Extract Amazon products from URL list. Each URL is corresponding to with a product.

        Args:
            url_list (list[str]): Product urls

        Returns:
            list[Item]: List of Item objects
        """

        if not url_list or len(url_list) == 0:
            return []

        for index in range(len(url_list)):

            self.driver.get(url_list[index])

            time.sleep(3.2)

            # Choose location according zipcode
            if index == 0:
                self.choose_location_to_delivery_to()

            self.driver.refresh()

            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # ID
            id = self.soup_try_to_find("input", {"id": "ASIN"})

            # CATEGORY_ASIN (get from parameter)

            # CATEGORY_NAME (get from parameter)

            # PRODUCT_ASIN
            

            print(f"ID: {id}")
            print(f"CATEGORY_ASIN: {category_asin}")
            print(f"CATEGORY_NAME: {category_name}")

            # # TITLE
            # title = self.soup_try_to_find("span", {"id": "productTitle"})

            # # AVAILIBILITY
            # avai = self.soup_try_to_find(
            #     "span", {"class": "a-size-medium a-color-success"}
            # )

            # # PRICE
            # price = float(
            #     re.findall(
            #         r"\d+\.\d+|\d+",
            #         self.soup_try_to_find("span", {"class": "aok-offscreen"}),
            #     )[0]
            # )

            # # DESCRIPTION
            # ul_element = self.soup.find(
            #     "ul", class_="a-unordered-list a-vertical a-spacing-mini"
            # )

            # # Find all <li> elements within the <ul>
            # li_elements = ul_element.find_all("li", class_="a-spacing-mini")

            # # Extract and print the descriptions from each <li> element
            # descriptions = [li.span.text.strip() for li in li_elements]

            # # RATING
            # rating = self.soup.find(
            #     "span",
            #     {"data-hook": "rating-out-of-text"},
            # ).text.strip()
            # if rating:
            #     rating = float(re.search(r"\d+(\.\d+)?", rating).group())

            # # REVIEWS
            # reviews = self.soup.find(
            #     "span", {"id": "acrCustomerReviewText"}
            # ).text.strip()
            # if reviews:
            #     reviews = int(re.match(r"\d+", reviews).group())


def extract_amazon_product_data_from_url(url: str, driver: WebDriver, zipcode: int):
    wait = WebDriverWait(driver, 10)

    driver.get(url)

    # Choose location according to zipcode
    wait.until(
        EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))
    ).click()
    wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-action='GLUXPostalInputAction']")
        )
    ).send_keys("92104")
    wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[aria-labelledby='GLUXZipUpdate-announce']")
        )
    ).click()
    wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".a-popover-footer #GLUXConfirmClose")
        )
    ).click()

    # Extract the product title (outside the loop as it's the same for all colors)
    product_title = (
        WebDriverWait(driver, 10)
        .until(EC.presence_of_element_located((By.ID, "productTitle")))
        .text
    )

    driver.refresh()

    # INITIALIZE_BS4
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # TITLE
    title = soup.find("span", {"id": "productTitle"}).text.strip()

    # AVAILIBILITY
    avai = soup.find("span", {"class": "a-size-medium a-color-success"}).text.strip()

    # PRICE
    price_whole = soup.find("span", {"class": "a-price-whole"}).text.strip()
    if price_whole:
        price_whole = int(re.match(r"\d+", price_whole).group())

    price_fraction = soup.find("span", {"class": "a-price-fraction"}).text.strip()

    price_unit = soup.find("span", {"class": "a-price-symbol"}).text.strip()

    # DESCRIPTION
    ul_element = soup.find("ul", class_="a-unordered-list a-vertical a-spacing-mini")

    # Find all <li> elements within the <ul>
    li_elements = ul_element.find_all("li", class_="a-spacing-mini")

    # Extract and print the descriptions from each <li> element
    descriptions = [li.span.text.strip() for li in li_elements]

    # RATING
    rating = soup.find(
        "span",
        {"data-hook": "rating-out-of-text"},
    ).text.strip()
    if rating:
        rating = float(re.search(r"\d+(\.\d+)?", rating).group())

    # REVIEWS
    reviews = soup.find("span", {"id": "acrCustomerReviewText"}).text.strip()
    if reviews:
        reviews = int(re.match(r"\d+", reviews).group())

    # PRINT INFO
    print(f"Title: {title}")
    print(f"Availability: {avai}")
    print(f"Price: {price_whole}.{price_fraction}")
    print(f"Price unit: {price_unit}")
    print(f"Descriptions: {descriptions}")
    print(f"Rating: {rating}")
    print(f"Reviews: {reviews}")


def main():
    URLs = [
        "https://www.amazon.com/COSIBONO-Pumpkin-Decorative-Harvest-Farmhouse/dp/B0D5YM77ML/ref=zg_bsnr_c_home-garden_d_sccl_4/141-3078590-5074935?pd_rd_w=D5QLJ&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=SFW6WCTP49M4KPEMC58E&pd_rd_wg=TrGpP&pd_rd_r=f059d5b7-30fb-485a-8a07-65c36aaaa1c3&pd_rd_i=B0D5YM77ML&th=1",
        # "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/141-3078590-5074935?pd_rd_w=TKw5q&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=FS98Z2RHTK16P5S8J7QC&pd_rd_wg=UAZ3a&pd_rd_r=3c539dc2-8a71-4ce0-9fa2-54e61e4b3277&pd_rd_i=B0CX18TFQD&th=1",
        # "https://www.amazon.com/FADAKWALT-Inflator-Portable-Compressor-Motorcycles/dp/B0D1MZ5ZTK/ref=zg_bsnr_c_automotive_d_sccl_2/141-3078590-5074935?pd_rd_w=TKw5q&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=FS98Z2RHTK16P5S8J7QC&pd_rd_wg=UAZ3a&pd_rd_r=3c539dc2-8a71-4ce0-9fa2-54e61e4b3277&pd_rd_i=B0D1MZ5ZTK&th=1",
    ]

    # OPTIONS = Options()
    # # OPTIONS.add_argument("--headless=new")

    # DRIVER = webdriver.Chrome(options=OPTIONS)

    # ZIPCODE = 92104

    # for URL in URLs:
    #     extract_amazon_product_data_from_url(URL, DRIVER, ZIPCODE)

    extractor = Extactor()
    extractor.extract_amazon_product_data_from_url(URLs)


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.5f} seconds")
