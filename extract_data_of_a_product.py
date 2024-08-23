from bs4 import BeautifulSoup
import requests
import re


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


if __name__ == "__main__":
    main()
