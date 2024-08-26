from playwright.sync_api import sync_playwright
import time

url = "https://www.amazon.com/Best-Sellers-Amazon-Devices-Accessories/zgbs/amazon-devices/ref=zg_bs_nav_amazon-devices_0"

start_time = time.time()

# Start Playwright
playwright = sync_playwright().start()

# Launch the browser
browser = playwright.chromium.launch(headless=True)

# Open a new page
page = browser.new_page()

# Go to the URL
page.goto(url)

# Wait for the page to fully load
page.wait_for_load_state("networkidle")

# Scroll down the page in increments
scroll_increment = 1000
total_scrolls = 20
for _ in range(total_scrolls):
    page.evaluate(f"window.scrollBy(0, {scroll_increment})")
    # Wait for a short time to allow new content to load
    page.wait_for_timeout(1000)  # Adjust the timeout if needed

# Select all elements with the specified XPath
elements = page.query_selector_all('//*[@class="a-link-normal aok-block"]')

index = 0

for element in elements:
    print(f"Link {index}: {element.get_attribute("href")}")
    index += 1


# Close the browser and stop Playwright
browser.close()
playwright.stop()

end_time = time.time()

elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time:.5f} seconds")
