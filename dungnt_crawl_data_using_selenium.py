"""
Created on Fri Aug 23 13:47:28 2024

@author: dungnguyen
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time

options = Options()

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

url = "https://www.amazon.com/Amelity-Headrest-Storage-Leather-Black-2/dp/B0CX18TFQD/ref=zg_bsnr_c_automotive_d_sccl_1/136-3737609-7879062?pd_rd_w=OPVDM&content-id=amzn1.sym.7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_p=7379aab7-0dd8-4729-b0b5-2074f1cb413d&pf_rd_r=YP1XSS0HMXZM3T7NZVJ1&pd_rd_wg=OgJkA&pd_rd_r=f6e34945-87f9-42f6-846e-12de137e8f40&pd_rd_i=B0CX18TFQD&th=1"
driver.get(url)

# Set location
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
    EC.element_to_be_clickable((By.CSS_SELECTOR, ".a-popover-footer #GLUXConfirmClose"))
).click()

# Extract the product title (outside the loop as it's the same for all colors)
product_title = (
    WebDriverWait(driver, 10)
    .until(EC.presence_of_element_located((By.ID, "productTitle")))
    .text
)

# Extract product rating
product_rating = driver.find_element(By.CSS_SELECTOR, ".a-icon-alt").text

# Extract the number of customer reviews
num_reviews = driver.find_element(By.ID, "acrCustomerReviewText").text

# Extract product description (example with first bullet point)
product_description = (
    WebDriverWait(driver, 10)
    .until(EC.visibility_of_element_located((By.ID, "feature-bullets")))
    .text
)


if product_description.endswith("and more\n› See more product details"):
    # Remove the specified text
    product_description = product_description[
        : -len("and more\n› See more product details")
    ]

# Extract last month sold
last_month_sold = (
    WebDriverWait(driver, 10)
    .until(
        EC.presence_of_element_located(
            (By.ID, "social-proofing-faceout-title-tk_bought")
        )
    )
    .text
)

# Store the product details for each color
product_data = []

# Find all available colors (if any)
color_elements = driver.find_elements(By.CSS_SELECTOR, "#variation_color_name li")

if len(color_elements) != 0:
    for i in range(len(color_elements)):
        # Re-locate the color elements to avoid StaleElementReferenceException
        color_elements = driver.find_elements(
            By.CSS_SELECTOR, "#variation_color_name li"
        )
        color_element = color_elements[i]

        # Click on each color variant
        color_element.click()

        # Add a short wait to ensure the page updates
        time.sleep(2)

        # Wait for the price element to update after color selection
        span_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-offscreen"))
        )

        # Extract the text content of the span element
        product_price = span_element.get_attribute("textContent")

        # Extract the selected color's name
        selected_color_name = driver.find_element(
            By.CSS_SELECTOR, "#variation_color_name .selection"
        ).text

        # Extract product status
        product_status = driver.find_element(By.ID, "availability").text

        # Append the data to the list
        product_data.append(
            {
                "Color": selected_color_name,
                "Price": product_price,
                "Status": product_status,
            }
        )

else:
    span_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-offscreen"))
    )

    # Extract the text content of the span element
    product_price = span_element.get_attribute("textContent")

    # Extract product status
    product_status = driver.find_element(By.ID, "availability").text


# Print the extracted details
print(f"Product Title: {product_title}")
print("\n")
print(f"Product Rating: {product_rating}")
print("\n")
print(f"Number of Reviews: {num_reviews}")
print("\n")
print(f"Product Description: {product_description}")
print("\n")
print(f"Last Month Sold: {last_month_sold}")
print("\n" + "=" * 50 + "\n")

if len(color_elements) != 0:
    # Print all extracted product data
    for data in product_data:
        print(f"Color: {data['Color']}")
        print(f"Product Price: {data['Price']}")
        print(f"Product Status: {data['Status']}")
        print("\n" + "=" * 50 + "\n")
else:
    print(f"Product Price: {product_price}")
    print(f"Product Status: {product_status}")

driver.quit()
