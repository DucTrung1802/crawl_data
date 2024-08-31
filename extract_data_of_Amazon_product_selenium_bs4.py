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
import json
from enum import Enum


class LogType(Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


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
        model: str,
        price: float,
        last_month_sold: int,
        status: str = None,
        created_date: datetime.datetime = datetime.datetime.now().isoformat(),
    ):
        self.category_asin: int = category_asin
        self.category_name: str = category_name
        self.product_asin: str = product_asin
        self.title: str = title
        self.review_num: int = review_num
        self.rating: float = rating
        self.description: str = description
        self.model: str = model
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
            f"model: {self.model}\n"
            f"PRICE: {self.price}\n"
            f"STATUS: {self.status}\n"
            f"LAST_MONTH_SOLD: {self.last_month_sold}\n"
            f"CREATED_DATE: {self.created_date}"
        )

    def to_dict(self):
        return {
            "category_asin": self.category_asin,
            "category_name": self.category_name,
            "product_asin": self.product_asin,
            "title": self.title,
            "review_num": self.review_num,
            "rating": self.rating,
            "description": self.description,
            "model": self.model,
            "price": self.price,
            "status": self.status,
            "last_month_sold": self.last_month_sold,
            "created_date": self.created_date,
        }


class Category:
    def __init__(self, url: str, category_asin: str, category_name: str):
        self.url: str = url
        self.category_asin: int = category_asin
        self.category_name: str = category_name
        self.product_list: list[Item] = []
        self.product_count: int = 0
        self.sub_category_list: list[Category] = []
        self.sub_category_count: int = 0


class Extactor:
    def __init__(self, zipcode=92104):
        self.driver_options = Options()

        self.driver = webdriver.Chrome(options=self.driver_options)

        self.wait = WebDriverWait(self.driver, 10)
        self.zipcode = zipcode

        self.amazon_base_url = "https://www.amazon.com"

        self.driver.get(self.amazon_base_url)
        self.apply_header()

        self.create_soup()

        self.sleep_interval = 1

        self.log_index = 1

        # INITIALIZE
        time.sleep(self.sleep_interval)

        self.check_and_bypass_amazon_captcha()
        self.choose_location_to_delivery_to(zipcode)

    def log(self, log_type: LogType, message: str):
        print(f"[{self.log_index:05}] {log_type.value} {message}")
        self.log_index += 1

    def apply_header(self):
        self.user_agents = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        self.driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": self.user_agents},
        )

        self.driver.execute_script("return navigator.userAgent;")

    def check_and_bypass_amazon_captcha(self):
        time.sleep(self.sleep_interval)

        self.create_soup()
        text = self.soup_try_to_find("h4")
        while text:
            captcha_image_link = self.soup_try_to_find("img", {}, "src")
            captcha = AmazonCaptcha.fromlink(captcha_image_link)
            solution = captcha.solve()
            self.driver.find_element(By.ID, "captchacharacters").send_keys(solution)
            self.driver.find_element(By.CLASS_NAME, "a-button-text").click()

            time.sleep(3)

            self.create_soup()
            text = self.soup_try_to_find("h4")

        time.sleep(self.sleep_interval)

    def choose_location_to_delivery_to(self, zipcode: int = 92104):
        if self.wait:

            self.create_soup()
            location = self.soup_try_to_find(
                "span", {"class": "nav-line-2 nav-progressive-content"}
            )

            while not location:
                self.driver.refresh()
                time.sleep(3)

                self.create_soup()
                location = self.soup_try_to_find(
                    "span", {"class": "nav-line-2 nav-progressive-content"}
                )

            while not str(zipcode) in location:
                self.wait.until(
                    EC.element_to_be_clickable(
                        (By.ID, "nav-global-location-popover-link")
                    )
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

                time.sleep(3)

                self.create_soup()
                location = self.soup_try_to_find(
                    "span", {"class": "nav-line-2 nav-progressive-content"}
                )

        time.sleep(1)

        self.driver.execute_script("window.stop();")

    def create_soup(self):
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

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
        self,
        name: str,
        attribute: dict = {},
        get_value_from_attribute: str = None,
        raw: bool = False,
    ):
        try:
            item_list = self.soup.find_all(name, attribute)
            if raw:
                return [item for item in item_list]
            else:
                if get_value_from_attribute:
                    return [item.get(get_value_from_attribute) for item in item_list]
                else:
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

        self.create_soup()

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

        # model
        model = self.soup_try_to_find("span", {"class": "selection"})

        # PRICE
        price = self.soup_try_to_find("span", {"class": "aok-offscreen"})
        if price:
            price = float(
                re.findall(
                    r"\d+\.\d+|\d+",
                    price,
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
        if last_month_sold:
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
        created_date = datetime.datetime.now().isoformat()

        return Item(
            category_asin=category_asin,
            category_name=category_name,
            product_asin=product_asin,
            title=title,
            review_num=review_num,
            rating=rating,
            description=description,
            model=model,
            price=price,
            status=status,
            last_month_sold=last_month_sold,
            created_date=created_date,
        )

    def handle_request_was_throttled(self):
        # Handle: Request was throttled. Please wait a moment and refresh the page
        time.sleep(2)

        self.create_soup()

        wait = WebDriverWait(self.driver, 5)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
            text = self.soup_try_to_find("pre")
            if text:
                time.sleep(3)
                self.driver.refresh()
        except:
            pass

    def get_asin_of_category(self, category_url: str):
        if not category_url or len(category_url) == 0:
            return -1

        match = re.search(r"/zgbs/.+?/(\d+)", category_url)
        if match:
            return match.group(1)
        return -1

    def get_name_of_category(self):
        text = self.soup_try_to_find(
            "h1", {"class": "a-size-large a-spacing-medium a-text-bold"}
        )
        if text:
            match = re.search(r"in (.*)", text)
            return match.group(1)

        return ""

    def get_product_urls_from_category_url(self, category_url: str):
        """
        Extract all product urls from a category url.

        Args:
            category_url (str): Category url
        """

        if not category_url or len(category_url) == 0:
            return []

        self.driver.get(category_url)

        self.handle_request_was_throttled()

        self.scroll_to_the_end_of_page_slowly()

        self.create_soup()

        product_urls = []
        product_urls.extend(
            self.soup_try_to_find_all("a", {"class": "a-link-normal aok-block"}, "href")
        )

        is_next_button_clickable = EC.element_to_be_clickable((By.CLASS_NAME, "a-last"))

        try:
            while is_next_button_clickable:
                self.wait.until(is_next_button_clickable).click()

                self.handle_request_was_throttled()

                time.sleep(2)

                self.scroll_to_the_end_of_page_slowly()

                self.create_soup()

                product_urls.extend(
                    self.soup_try_to_find_all(
                        "a", {"class": "a-link-normal aok-block"}, "href"
                    )
                )

                if EC.presence_of_element_located((By.CLASS_NAME, "a-disabled a-last")):
                    break
        except Exception as ex:
            self.log(LogType.INFO, "No 'Next page' button to click")

        return product_urls

    def extract_all_products_from_current_category(
        self, category_url: str, category_asin: str, category_name: str
    ):
        if not category_url or len(category_url) == 0:
            return []

        product_url_list = self.get_product_urls_from_category_url(category_url)
        product_list: list[Item] = []
        pattern = r"/dp/([A-Z0-9]+)"

        for product_url in product_url_list:
            try:
                match = re.search(pattern, product_url)
                if match:
                    product_code = match.group(1)
                    self.log(
                        LogType.INFO, f"Extracting product with ASIN: {product_code}"
                    )
                    complete_url = self.amazon_base_url + product_url
                    product_list.append(
                        self.extract_amazon_product_from_url(
                            complete_url, category_asin, category_name
                        )
                    )
            except Exception as e:
                self.log(LogType.ERROR, e)

        self.log(
            LogType.INFO,
            f"Extracted {len(product_list)}/{len(product_url_list)} products of this category!",
        )
        if len(product_url_list) > 0 and len(product_list) < len(product_url_list):
            self.log(
                LogType.WARN,
                f"Cannot extract products of this category with url: {category_url}",
            )

        return product_list

    def get_sub_categories_link_list_of_current_category(self, category_url: str):
        if not category_url and len(category_url) == 0:
            return []

        self.driver.get(category_url)

        self.create_soup()

        try:
            group_divs = self.soup_try_to_find(
                "div", {"role": "group"}, None, True
            ).find_all("div")

            href_links = []
            for group_div in group_divs:
                a_tag = group_div.find("a")
                if not a_tag or not a_tag["href"]:
                    return []

                href_links.append(self.amazon_base_url + a_tag["href"])

            return href_links

        except:
            return []

    def get_all_nested_products_of_category(
        self, category_url: str, category_asin: str, category_name: str
    ):
        pass

    def output_to_json(self, category: Category, file_name: str):
        if not file_name or len(file_name) == 0:
            self.log(LogType.ERROR, "No file name specified!")
            raise Exception("No file name specified!")

        file_name = file_name.lower().replace(" ", "_")

        output_dictionary: dict = {}

        output_dictionary["category_asin"] = category.category_asin
        output_dictionary["category_name"] = category.category_name
        output_dictionary["product_list"] = [
            item.to_dict() for item in category.product_list
        ]
        output_dictionary["product_count"] = category.product_count
        output_dictionary["sub_category_count"] = category.sub_category_count

        with open(f"{file_name}.json", "w") as file:
            json.dump(output_dictionary, file, indent=4)


def main():
    URL = "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/141-3078590-5074935?pd_rd_w=MABN3&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=0Y582SYJA52XPQ46D08Z&pd_rd_wg=WBZ2b&pd_rd_r=d16f64de-fd58-48a9-b10c-27becea887e2&pd_rd_i=B0CX18TFQD&th=1"

    extractor = Extactor()

    # new_product = extractor.extract_amazon_product_from_url(URL)
    # print(new_product)

    # new_category = Category(
    #     url="https://www.amazon.com/gp/new-releases/amazon-devices/17942903011/ref=zg_bsnr_nav_amazon-devices_2_1289283011",
    #     category_asin=17942903011,
    #     category_name="New Releases in Amazon Device Adapters & Connectors",
    # )

    # new_category.product_list = extractor.extract_all_products_from_current_category(
    #     new_category.url, new_category.category_asin, new_category.category_name
    # )
    # new_category.product_count = len(new_category.product_list)

    # extractor.output_to_json(new_category, "New Releases in Amazon Device Accessories")

    # CATEGORY_URL = "https://www.amazon.com/Best-Sellers-Amazon-Devices-Accessories-Amazon-Device-Audio-Accessories/zgbs/amazon-devices/1289283011/ref=zg_bs_nav_amazon-devices_2_17942903011"
    # extractor.driver.get(CATEGORY_URL)
    # extractor.create_soup()
    # print(f"Category name: {extractor.get_name_of_category()}")
    # links = extractor.get_sub_categories_link_list_of_current_category(CATEGORY_URL)


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.5f} seconds")
