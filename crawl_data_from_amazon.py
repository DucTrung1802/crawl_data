from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np

# SETUP PARAMETERS

HEADERS = {"User-Agent": "", "Accept-Language": "en-US, en;q=0.5"}

BEST_SELLERS_URL = "https://www.amazon.com/Best-Sellers/zgbs/ref=zg_bs_tab_bs"

NEW_RELEASES_URL = "https://www.amazon.com/gp/new-releases/ref=zg_bs_tab_bsnr"


# DATA MODELS
class Item:
    def __init__(self):
        self.title: str = ""
        self.price: float = 0.0
        self.price_unit: str = ""
        self.availablity: bool = True
        self.description: str = ""
        self.rating: float = 0.0
        self.reviews: int = 0


class Department:
    def __init__(self, url):
        self.url: str = url
        self.list_of_items: list[Item] = []
        self.list_of_sub_departments: list[Department] = []


# CRAWL DATA FUNCTIONS


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
    crawl_data_from_best_sellers(BEST_SELLERS_URL, HEADERS)

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
