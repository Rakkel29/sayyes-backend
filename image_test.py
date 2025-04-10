import asyncio
import json
from crawl_tools import get_images_from_url, get_local_images
from sayyes_agent import get_wedding_images

async def test_web_crawling():
    print("=== Testing Web Crawling ===")
    # Test crawling wedding venues
    url = "https://www.weddingwire.com/c/tx-texas/austin/wedding-venues/11-vendors.html"
    print(f"\nCrawling URL: {url}")
    
    try:
        image_urls = await get_images_from_url(url)
        print(f"Found {len(image_urls)} images")
        print("First 3 images:")
        for i, url in enumerate(image_urls[:3]):
            print(f"  {i+1}. {url}")
    except Exception as e:
        print(f"Error during web crawling: {e}")

def test_local_fallbacks():
    print("\n=== Testing Local Fallbacks ===")
    
    categories = ["venues", "dresses", "hairstyles"]
    for category in categories:
        print(f"\nTesting local fallbacks for {category}")
        images = get_local_images(category)
        print(f"Found {len(images)} local images for {category}")
        if images:
            print("First image:")
            for key, value in images[0].items():
                print(f"  {key}: {value}")

def test_integrated_tool():
    print("\n=== Testing Integrated Tool ===")
    
    categories = ["venues", "dresses", "hairstyles"]
    for category in categories:
        print(f"\nTesting integrated tool for {category}")
        result = get_wedding_images(category)
        images = json.loads(result)
        print(f"Found {len(images)} images for {category}")
        if images:
            print("First image:")
            for key, value in images[0].items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_web_crawling())
    
    # Run the local fallback test
    test_local_fallbacks()
    
    # Test the integrated tool
    test_integrated_tool() 