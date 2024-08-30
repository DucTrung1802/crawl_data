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
        self.apply_header()

        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

        self.sleep_interval = 1

        # INITIALIZE
        time.sleep(self.sleep_interval)

        self.check_and_bypass_amazon_captcha()
        self.choose_location_to_delivery_to(zipcode)

    def apply_header(self):
        self.user_agents = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        self.driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": self.user_agents},
        )

        self.driver.execute_script("return navigator.userAgent;")

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

        time.sleep(1)

        self.driver.execute_script("window.stop();")

    def soup_try_to_find(
        self,
        name: str,
        attribute: dict = {},
        get_value_from_attribute: str = None,
        raw: bool = False,
    ):
        try:
            if raw:
                return self.soup.find(name, attribute)
            else:
                if get_value_from_attribute:
                    return self.soup.find(name, attribute).get(get_value_from_attribute)
                else:
                    return self.soup.find(name, attribute).text.strip()
        except:
            return None

    def soup_try_to_find_all(
        self, name: str, attribute: dict = {}, get_value_from_attribute: str = None
    ):
        try:
            if get_value_from_attribute:
                item_list = self.soup.find_all(name, attribute)
                return [item.get(get_value_from_attribute) for item in item_list]
            else:
                item_list = self.soup.find_all(name, attribute)
                return [item.text.strip() for item in item_list]
        except:
            return None

    def scroll_to_the_end_of_page_slowly(self):
        if not self.driver:
            return

        scroll_increment = 400  # Number of pixels to scroll each time
        scroll_pause_time = 0.5  # Pause time between scrolls (in seconds)

        # Get the total height of the page
        total_height = self.driver.execute_script("return document.body.scrollHeight")

        current_position = 0
        while current_position < total_height:
            # Scroll down by 'scroll_increment' pixels
            self.driver.execute_script(f"window.scrollBy(0, {scroll_increment});")

            # Update the current position
            current_position += scroll_increment

            # Wait for a short time before scrolling again
            time.sleep(scroll_pause_time)

            # Update total height in case the content loads dynamically (infinite scrolling)
            total_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

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

    def get_product_urls_from_current_category(self, category_url: str):
        """
        Extract all product urls from a category url.

        Args:
            category_url (str): Category url
        """

        if not category_url or len(category_url) == 0:
            return []

        self.driver.get(category_url)

        time.sleep(2)

        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Handle: Request was throttled. Please wait a moment and refresh the page
        wait = WebDriverWait(self.driver, 5)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
            text = self.soup_try_to_find("pre")
            if text:
                time.sleep(3)
                self.driver.refresh()
        except:
            pass

        self.scroll_to_the_end_of_page_slowly()

        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

        product_urls = []
        product_urls.extend(
            self.soup_try_to_find_all("a", {"class": "a-link-normal aok-block"}, "href")
        )

        is_next_button_clickable = EC.element_to_be_clickable((By.CLASS_NAME, "a-last"))

        while is_next_button_clickable:
            self.wait.until(is_next_button_clickable).click()

            time.sleep(3)

            self.scroll_to_the_end_of_page_slowly()

            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

            product_urls.extend(
                self.soup_try_to_find_all(
                    "a", {"class": "a-link-normal aok-block"}, "href"
                )
            )

            if EC.presence_of_element_located((By.CLASS_NAME, "a-disabled a-last")):
                break

        return product_urls


def main():
    URL = "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/141-3078590-5074935?pd_rd_w=MABN3&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=0Y582SYJA52XPQ46D08Z&pd_rd_wg=WBZ2b&pd_rd_r=d16f64de-fd58-48a9-b10c-27becea887e2&pd_rd_i=B0CX18TFQD&th=1"

    CATEGORY_URL = "https://www.amazon.com/Best-Sellers-Amazon-Devices-Accessories-Amazon-Device-Accessories/zgbs/amazon-devices/370783011/ref=zg_bs_unv_amazon-devices_2_1289283011_2"

    extractor = Extactor()

    # new_product = extractor.extract_amazon_product_from_url(URL)
    # print(new_product)

    product_urls_list = extractor.get_product_urls_from_current_category(CATEGORY_URL)
    print(product_urls_list)
    print(len(product_urls_list))


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.5f} seconds")
