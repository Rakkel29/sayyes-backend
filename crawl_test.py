import asyncio
from crawl_tools import get_images_from_url

if __name__ == "__main__":
    url = "https://www.weddingwire.com/c/tx-texas/austin/wedding-venues/11-vendors.html"
    images = asyncio.run(get_images_from_url(url))
    for img in images[:5]:  # limit to first 5
        print(img) 