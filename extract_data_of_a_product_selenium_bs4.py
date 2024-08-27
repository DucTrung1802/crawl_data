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

    driver.quit()


def main():
    URLs = [
        "https://www.amazon.com/COSIBONO-Pumpkin-Decorative-Harvest-Farmhouse/dp/B0D5YM77ML/ref=zg_bsnr_c_home-garden_d_sccl_4/141-3078590-5074935?pd_rd_w=D5QLJ&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=SFW6WCTP49M4KPEMC58E&pd_rd_wg=TrGpP&pd_rd_r=f059d5b7-30fb-485a-8a07-65c36aaaa1c3&pd_rd_i=B0D5YM77ML&th=1",
        "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/141-3078590-5074935?pd_rd_w=TKw5q&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=FS98Z2RHTK16P5S8J7QC&pd_rd_wg=UAZ3a&pd_rd_r=3c539dc2-8a71-4ce0-9fa2-54e61e4b3277&pd_rd_i=B0CX18TFQD&th=1",
        "https://www.amazon.com/FADAKWALT-Inflator-Portable-Compressor-Motorcycles/dp/B0D1MZ5ZTK/ref=zg_bsnr_c_automotive_d_sccl_2/141-3078590-5074935?pd_rd_w=TKw5q&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=FS98Z2RHTK16P5S8J7QC&pd_rd_wg=UAZ3a&pd_rd_r=3c539dc2-8a71-4ce0-9fa2-54e61e4b3277&pd_rd_i=B0D1MZ5ZTK&th=1",
    ]

    OPTIONS = Options()
    # OPTIONS.add_argument("--headless=new")

    DRIVER = webdriver.Chrome(options=OPTIONS)

    ZIPCODE = 92104

    for URL in URLs:
        extract_amazon_product_data_from_url(URL, DRIVER, ZIPCODE)


if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.5f} seconds")
