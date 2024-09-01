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


class SelectionType(Enum):
    RAW = 0
    TEXT = 1
    ATTRIBUTE = 2


class ElementToFind:
    def __init__(
        self,
        name: str,
        attributes: dict = {},
        selection_type: SelectionType = SelectionType.RAW,
        get_value_from_attribute: str = "",
    ):
        self.name = name
        self.attributes = attributes
        self.selection_type = selection_type

        if (
            selection_type == SelectionType.ATTRIBUTE
            and len(get_value_from_attribute) == 0
        ):
            raise ValueError(
                f"get_value_from_attribute must not be empty string when selection_type is SelectionType.ATTRIBUTE"
            )
        self.get_value_from_attribute = get_value_from_attribute


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
    def __init__(self, url: str, category_asin: int = -1, category_name: str = ""):
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

        self.get_url(self.amazon_base_url)
        self.apply_header()

        self.create_soup()

        self.sleep_interval = 1

        # INITIALIZE
        time.sleep(self.sleep_interval)

        self.check_and_bypass_amazon_captcha()
        self.choose_location_to_delivery_to(zipcode)

    def log(self, log_type: LogType, message: str):
        print(f"{datetime.datetime.now()} {log_type.value} {message}")

    def apply_header(self):
        self.user_agents = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        self.driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": self.user_agents},
        )

        self.driver.execute_script("return navigator.userAgent;")

    def get_url(self, url: str):
        if not url or len(url) == 0:
            return

        self.driver.get(url)

        time.sleep(3)

        self.handle_request_was_throttled()

    def check_and_bypass_amazon_captcha(self):
        time.sleep(self.sleep_interval)

        self.create_soup()
        text = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(name="h4", selection_type=SelectionType.TEXT)
            ],
        )
        while text:
            captcha_image_link = self.soup_try_to_find(
                possible_element_to_find_list=[
                    ElementToFind(
                        name="img",
                        selection_type=SelectionType.ATTRIBUTE,
                        get_value_from_attribute="src",
                    )
                ]
            )
            captcha = AmazonCaptcha.fromlink(captcha_image_link)
            solution = captcha.solve()
            self.driver.find_element(By.ID, "captchacharacters").send_keys(solution)
            self.driver.find_element(By.CLASS_NAME, "a-button-text").click()

            time.sleep(3)

            self.create_soup()
            text = self.soup_try_to_find(
                possible_element_to_find_list=[
                    ElementToFind(
                        name="h4",
                        selection_type=SelectionType.TEXT,
                    )
                ],
            )

        time.sleep(self.sleep_interval)

    def choose_location_to_delivery_to(self, zipcode: int = 92104):
        if self.wait:

            self.create_soup()

            location = self.soup_try_to_find(
                possible_element_to_find_list=[
                    ElementToFind(
                        name="span",
                        attributes={"class": "nav-line-2 nav-progressive-content"},
                        selection_type=SelectionType.TEXT,
                    )
                ],
            )

            while not location:
                self.driver.refresh()
                time.sleep(3)

                self.create_soup()

                location = self.soup_try_to_find(
                    possible_element_to_find_list=[
                        ElementToFind(
                            name="span",
                            attributes={"class": "nav-line-2 nav-progressive-content"},
                            selection_type=SelectionType.TEXT,
                        )
                    ],
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
                    possible_element_to_find_list=[
                        ElementToFind(
                            name="span",
                            attributes={"class": "nav-line-2 nav-progressive-content"},
                            selection_type=SelectionType.TEXT,
                        )
                    ],
                )

        time.sleep(1)

        self.driver.execute_script("window.stop();")

    def create_soup(self):
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def soup_try_to_find(
        self,
        possible_element_to_find_list: list[ElementToFind],
    ):
        try:
            for element in possible_element_to_find_list:
                match element.selection_type:
                    case SelectionType.RAW:
                        output = self.soup.find(element.name, element.attributes)

                    case SelectionType.TEXT:
                        output = self.soup.find(
                            element.name, element.attributes
                        ).text.strip()

                    case SelectionType.ATTRIBUTE:
                        output = self.soup.find(element.name, element.attributes).get(
                            element.get_value_from_attribute
                        )

                if output:
                    return output

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

        self.get_url(product_url)

        self.create_soup()

        # CATEGORY_ASIN (get from parameter)

        # CATEGORY_NAME (get from parameter)

        # PRODUCT_ASIN
        product_asin = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="input",
                    attributes={"id": "ASIN"},
                    selection_type=SelectionType.ATTRIBUTE,
                    get_value_from_attribute="value",
                ),
                ElementToFind(
                    name="input",
                    attributes={"id": "all-offers-display-params"},
                    selection_type=SelectionType.ATTRIBUTE,
                    get_value_from_attribute="data-asin",
                ),
            ],
        )

        # TITLE
        title = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"id": "productTitle"},
                    selection_type=SelectionType.TEXT,
                ),
                ElementToFind(
                    name="span",
                    attributes={"id": "ebooksProductTitle"},
                    selection_type=SelectionType.TEXT,
                ),
            ]
        )

        # REVIEWS
        review_num = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"id": "acrCustomerReviewText"},
                    selection_type=SelectionType.TEXT,
                )
            ]
        )
        if review_num:
            review_num = int(re.sub(r"[^\d]", "", review_num))

        # RATING
        rating = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"data-hook": "rating-out-of-text"},
                    selection_type=SelectionType.TEXT,
                )
            ]
        )
        if rating:
            rating = float(re.search(r"\d+(\.\d+)?", rating).group())

        # DESCRIPTION
        ul_element = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="ul",
                    attributes={"class": "a-unordered-list a-vertical a-spacing-mini"},
                    selection_type=SelectionType.RAW,
                )
            ]
        )
        description = []
        if ul_element:
            li_elements = ul_element.find_all("li", class_="a-spacing-mini")
            for li in li_elements:
                description.append(li.text.strip())

        # MODEL
        model = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"class": "selection"},
                    selection_type=SelectionType.TEXT,
                )
            ]
        )

        # PRICE
        price = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"class": "aok-offscreen"},
                    selection_type=SelectionType.TEXT,
                ),
                ElementToFind(
                    name="span",
                    attributes={"class": "a-size-medium a-color-price a-text-normal"},
                    selection_type=SelectionType.TEXT,
                ),
            ]
        )
        if price:
            price = float(
                re.findall(
                    r"\d+\.\d+|\d+",
                    price,
                )[0]
            )

        # STATUS
        status = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"class": "a-size-medium a-color-success"},
                    selection_type=SelectionType.TEXT,
                )
            ]
        )

        # LAST MONTH SOLD
        last_month_sold = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="span",
                    attributes={"id": "social-proofing-faceout-title-tk_bought"},
                    selection_type=SelectionType.TEXT,
                )
            ]
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
            text = self.soup_try_to_find(
                possible_element_to_find_list=[
                    ElementToFind(name="pre", selection_type=SelectionType.TEXT)
                ],
            )
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
            return int(match.group(1))
        return -1

    def get_name_of_category(self):
        text = self.soup_try_to_find(
            possible_element_to_find_list=[
                ElementToFind(
                    name="h1",
                    attributes={"class": "a-size-large a-spacing-medium a-text-bold"},
                    selection_type=SelectionType.TEXT,
                )
            ]
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

        self.get_url(category_url)

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

    def extract_all_products_from_product_url_list(
        self,
        product_url_list: list[str],
        category_asin: int = -1,
        category_name: str = "",
    ):
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
                            complete_url,
                            category_asin=category_asin,
                            category_name=category_name,
                        )
                    )

            except Exception as e:
                self.log(LogType.ERROR, e)

        self.log(
            LogType.INFO,
            f"Extracted {len(product_list)}/{len(product_url_list)} products of category {category_name}",
        )

        if len(product_url_list) > 0 and len(product_list) < len(product_url_list):
            self.log(
                LogType.WARN,
                f"Cannot extract all products of category {category_name}",
            )

        return product_list

    def get_sub_categories_link_list_of_current_category(self, category_url: str):
        if not category_url and len(category_url) == 0:
            return []

        self.get_url(category_url)

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

    def get_all_products_and_nested_sub_catgories_of_current_category(
        self, category: Category
    ):
        if not category:
            self.log(LogType.ERROR, "Input must be a Category object")
            return

        if not category.url or len(category.url) == 0:
            self.log(LogType.ERROR, "Url of category must not be empty string")

        # Access to url of category
        self.get_url(category.url)

        self.create_soup()

        category.category_asin = self.get_asin_of_category(category.url)

        if not category.category_name or len(category.category_name) == 0:
            category.category_name = self.get_name_of_category()

        # Get all product urls
        product_url_list = self.get_product_urls_from_category_url(category.url)

        category.product_list = self.extract_all_products_from_product_url_list(
            product_url_list, category.category_asin, category.category_name
        )

        sub_categories_link_list = (
            self.get_sub_categories_link_list_of_current_category(category.url)
        )

        for sub_categories_link in sub_categories_link_list:
            sub_category = Category(sub_categories_link)
            sub_category = (
                self.get_all_products_and_nested_sub_catgories_of_current_category(
                    sub_category
                )
            )
            category.sub_category_list.append(sub_category)

        return category

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
    extractor = Extactor()

    # _1_layer_category = Category(
    #     url="https://www.amazon.com/Best-Sellers-Amazon-Devices-Accessories-Home-Security-Solar-Chargers/zgbs/amazon-devices/23581299011/ref=zg_bs_nav_amazon-devices_2_16958810011",
    #     category_asin=23581299011,
    #     category_name="Home Security Solar Chargers",
    # )

    # _1_layer_category = (
    #     extractor.get_all_products_and_nested_sub_catgories_of_current_category(
    #         _1_layer_category
    #     )
    # )

    # extractor.output_to_json(_1_layer_category, "Home Security Solar Chargers")

    _2_layer_category = Category(
        url="https://www.amazon.com/Best-Sellers-Kindle-Store-Technology-eMagazines/zgbs/digital-text/2460165011/ref=zg_bs_nav_digital-text_3_241646011",
        category_asin=2460165011,
        category_name="Technology eMagazines",
    )

    _2_layer_category = (
        extractor.get_all_products_and_nested_sub_catgories_of_current_category(
            _2_layer_category
        )
    )

    _2_layer_category = extractor.output_to_json(
        _2_layer_category, "Technology eMagazines"
    )


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.5f} seconds")
