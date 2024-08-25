from selenium import webdriver
from selenium.webdriver.remote.webdriver import (
    WebDriver,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
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
    ).send_keys(zipcode)
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

    # PRODUCT TITLE
    product_title = wait.until(
        EC.presence_of_element_located((By.ID, "productTitle"))
    ).text

    # PRODUCT RATING
    product_rating = driver.find_element(By.CSS_SELECTOR, ".a-icon-alt").text

    # NUMBER OF REVIEWS
    num_reviews = driver.find_element(By.ID, "acrCustomerReviewText").text

    # PRODUCT DESCRIPTIONS
    product_description = wait.until(
        EC.visibility_of_element_located((By.ID, "feature-bullets"))
    ).text
    if product_description.endswith("\n› See more product details"):
        # Remove the specified text
        product_description = product_description[
            : -len("\n› See more product details")
        ]

    # LAST MONTH SOLD
    last_month_sold = wait.until(
        EC.presence_of_element_located(
            (By.ID, "social-proofing-faceout-title-tk_bought")
        )
    ).text


def main():
    URL = "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/136-3737609-7879062?pd_rd_w=OPVDM&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=YP1XSS0HMXZM3T7NZVJ1&pd_rd_wg=OgJkA&pd_rd_r=f6e34945-87f9-42f6-846e-12de137e8f40&pd_rd_i=B0CX18TFQD&th=1"

    OPTIONS = Options()

    DRIVER = webdriver.Chrome(options=OPTIONS)

    ZIPCODE = 92104

    extract_amazon_product_data_from_url(URL, DRIVER, ZIPCODE)


if __name__ == "__main__":
    main()
