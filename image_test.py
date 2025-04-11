import asyncio
import json
from crawl_tools import get_images_from_url, get_local_images
from sayyes_agent import get_wedding_images
from blob_images import get_images_by_category

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

def test_get_wedding_images():
    """Test the get_wedding_images function with different categories"""
    categories = ["venues", "dresses", "hairstyles", "cakes"]
    
    for category in categories:
        print(f"\nTesting {category} images:")
        result = get_wedding_images(category)
        images = json.loads(result)
        
        if not images:
            print(f"No images found for {category}")
            continue
        
        print(f"Found {len(images)} images")
        
        # Print the first image details
        if images:
            first_image = images[0]
            print(f"First image: {first_image.get('title', 'No title')}")
            print(f"Image URL: {first_image.get('image', 'No URL')}")
            print(f"Description: {first_image.get('description', 'No description')}")
            
            # Print additional fields based on category
            if category == "venues":
                print(f"Location: {first_image.get('location', 'No location')}")
                print(f"Price: {first_image.get('price', 'No price')}")
            elif category == "dresses":
                print(f"Designer: {first_image.get('designer', 'No designer')}")
                print(f"Price: {first_image.get('price', 'No price')}")
            elif category == "cakes":
                print(f"Price: {first_image.get('price', 'No price')}")
            
            print(f"Tags: {first_image.get('tags', [])}")

def test_get_images_by_category():
    """Test the get_images_by_category function directly"""
    categories = ["venues", "dresses", "hairstyles", "cakes"]
    styles = ["rustic", "modern", "bohemian", "luxury", "classic"]
    locations = ["Austin", "New York", "Los Angeles"]
    
    # Test each category
    for category in categories:
        print(f"\nTesting {category} images:")
        images = get_images_by_category(category)
        
        if not images:
            print(f"No images found for {category}")
            continue
        
        print(f"Found {len(images)} images")
        
        # Print the first image details
        if images:
            first_image = images[0]
            print(f"First image: {first_image.get('title', 'No title')}")
            print(f"Image URL: {first_image.get('image', 'No URL')}")
    
    # Test with style filter
    print("\nTesting with style filter:")
    for style in styles:
        print(f"\nStyle: {style}")
        images = get_images_by_category("venues", style=style)
        if images:
            print(f"Found {len(images)} images with style '{style}'")
            print(f"First image: {images[0].get('title', 'No title')}")
    
    # Test with location filter
    print("\nTesting with location filter:")
    for location in locations:
        print(f"\nLocation: {location}")
        images = get_images_by_category("venues", location=location)
        if images:
            print(f"Found {len(images)} images for location '{location}'")
            print(f"First image: {images[0].get('title', 'No title')}")
            print(f"Location: {images[0].get('location', 'No location')}")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_web_crawling())
    
    # Run the local fallback test
    test_local_fallbacks()
    
    # Test the get_wedding_images function
    test_get_wedding_images()
    
    # Test the get_images_by_category function directly
    test_get_images_by_category() 