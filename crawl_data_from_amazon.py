from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import re

# SETUP PARAMETERS

BEST_SELLERS_URL = "https://www.amazon.com/Best-Sellers/zgbs/ref=zg_bs_tab_bs"

NEW_RELEASES_URL = "https://www.amazon.com/gp/new-releases/ref=zg_bs_tab_bsnr"


# DATA MODELS
class Item:
    def __init__(self):
        self.title: str = ""
        self.availablity: bool = True
        self.price: float = 0.0
        self.price_unit: str = ""
        self.description: str = ""
        self.rating: float = 0.0
        self.reviews: int = 0


class Department:
    def __init__(self, url):
        self.url: str = url
        self.list_of_items: list[Item] = []
        self.list_of_sub_departments: list[Department] = []


# CRAWL DATA FUNCTIONS


def set_zip_code(session, zip_code):
    # Amazon's endpoint to update the zip code might look something like this.
    # The actual endpoint and required data can be different and should be identified using browser developer tools.
    zip_code_url = "https://www.amazon.com/gp/delivery/ajax/address-change.html"

    # Payload for setting the zip code
    payload = {
        "locationType": "LOCATION_INPUT",
        "zipCode": zip_code,
        "storeContext": "generic",
        "deviceType": "web",
        "pageType": "Detail",
        "actionSource": "glow",
    }

    # Send POST request to set the zip code
    response = session.post(zip_code_url, data=payload)

    if response.status_code == 200:
        print(f"Zip code {zip_code} set successfully.")
    else:
        print("Failed to set zip code.")


def extract_amazon_product_from_url(session, url):
    try:
        webpage = session.get(url)
        soup = BeautifulSoup(webpage.content, "html.parser")

        print(f"URL: {url}")

        # TITLE
        title = soup.find("span", {"id": "productTitle"}).text.strip()

        # AVAILIBILITY
        avai = soup.find(
            "span", {"class": "a-size-medium a-color-success"}
        ).text.strip()

        # PRICE
        price_whole = soup.find("span", {"class": "a-price-whole"}).text.strip()
        if price_whole:
            price_whole = int(re.match(r"\d+", price_whole).group())

        price_fraction = soup.find("span", {"class": "a-price-fraction"}).text.strip()

        price_unit = soup.find("span", {"class": "a-price-symbol"}).text.strip()

        # DESCRIPTION
        ul_element = soup.find(
            "ul", class_="a-unordered-list a-vertical a-spacing-mini"
        )

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

        if title:
            print(f"Title: {title}")
        else:
            raise ValueError("Cannot crawl title")

        if avai:
            print(f"Availability: {avai}")
        else:
            raise ValueError("Cannot crawl availability")

        print(f"Price: {price_whole}.{price_fraction}")
        print(f"Price unit: {price_unit}")
        print(f"Descriptions: {descriptions}")
        print(f"Rating: {rating}")
        print(f"Reviews: {reviews}")

    except Exception as e:
        print(f"Logging: Error - {str(e)}")


def crawl_data_from_best_sellers(url: str, headers: str):
    try:
        webpage = requests.get(url=url, headers=headers)

        soup = BeautifulSoup(webpage.content, "html.parser")

        best_sellers_departments = []

        departments_doc = soup.find_all(
            "div",
            attrs={"role": "treeitem"},
        )

        # Loop for extracting links from Tag objects
        for department in departments_doc:
            # Find the <a> tag within the div
            a_tag = department.find("a")
            if a_tag and "href" in a_tag.attrs:
                # Append the href attribute to the list
                best_sellers_departments.append(Department(a_tag["href"]))

        print(best_sellers_departments)

        for department in best_sellers_departments:
            print(department.url)

    except:
        print(f"Couldn't get data from {url}")
        return


def main():
    PRODUCT_URL = "https://www.amazon.com/eero-Ethernet-Supports-gigabit-Midnight/dp/B0CGWSQJ29/ref=zg_bsnr_g_17942903011_d_sccl_3/141-3078590-5074935?psc=1"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US",
    }

    # New York zip code
    ZIP_CODE = 10001

    session = requests.Session()
    session.headers.update(HEADERS)

    set_zip_code(session, str(ZIP_CODE))

    extract_amazon_product_from_url(session, PRODUCT_URL)

    # crawl_data_from_best_sellers(BEST_SELLERS_URL, HEADERS)

    # d = {"title": [], "price": [], "rating": [], "reviews": [], "availability": []}

    # # Loop for extracting product details from each link
    # for link in links_list:
    #     new_webpage = requests.get("https://www.amazon.com" + link, headers=HEADERS)

    #     new_soup = BeautifulSoup(new_webpage.content, "html.parser")

    #     Function calls to display all necessary product information
    #     d["title"].append(get_title(new_soup))
    #     d["price"].append(get_price(new_soup))
    #     d["rating"].append(get_rating(new_soup))
    #     d["reviews"].append(get_review_count(new_soup))
    #     d["availability"].append(get_availability(new_soup))

    # amazon_df = pd.DataFrame.from_dict(d)
    # amazon_df["title"].replace("", np.nan, inplace=True)
    # amazon_df = amazon_df.dropna(subset=["title"])
    # amazon_df.to_csv("amazon_data.csv", header=True, index=False)


if __name__ == "__main__":
    main()
