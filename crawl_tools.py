from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import os
import glob

async def get_images_from_url(url: str) -> list[str]:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        # Get the HTML content from the result
        html_content = result[0].html
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all image tags and extract their src attributes
        image_tags = soup.find_all('img')
        image_urls = [img.get('src') for img in image_tags if img.get('src')]
        
        return image_urls

def get_local_images(category: str) -> list[dict]:
    """
    Get local fallback images for a specific category.
    
    Args:
        category: Type of images (venues, dresses, hairstyles)
        
    Returns:
        List of dictionaries with image information
    """
    base_dir = os.path.join('assets', category)
    
    # Check if directory exists
    if not os.path.exists(base_dir):
        return []
    
    # Get all image files in the directory
    image_files = glob.glob(os.path.join(base_dir, '*.jpg')) + glob.glob(os.path.join(base_dir, '*.png'))
    
    # Create result list with file paths and basic descriptions
    result = []
    for i, img_path in enumerate(image_files):
        filename = os.path.basename(img_path)
        name = os.path.splitext(filename)[0]
        
        # Create a description based on filename
        if category == 'venues':
            title = name.title()
            description = f"Beautiful {name} wedding venue"
            result.append({
                "image": img_path,
                "title": title,
                "description": description,
                "location": "Various locations",
                "price": "$$$" if i % 3 == 0 else ("$$" if i % 3 == 1 else "$"),
                "tags": ["Elegant", "Venue", "Wedding"]
            })
        elif category == 'dresses':
            title = f"Designer Dress {i+1}"
            description = f"Elegant {name} wedding dress"
            result.append({
                "image": img_path,
                "title": title,
                "description": description,
                "designer": "Designer Collection",
                "price": "$$$" if i % 3 == 0 else ("$$" if i % 3 == 1 else "$"),
                "tags": ["Elegant", "Dress", "Wedding"]
            })
        elif category == 'hairstyles':
            title = f"Hairstyle {i+1}"
            description = f"Stunning {name} wedding hairstyle"
            result.append({
                "image": img_path,
                "title": title,
                "description": description,
                "tags": ["Elegant", "Hairstyle", "Wedding"]
            })
        else:
            # Generic format for other categories
            title = f"{category.title()} {i+1}"
            description = f"{name.title()} for weddings"
            result.append({
                "image": img_path,
                "title": title,
                "description": description,
                "tags": ["Wedding", category.title()]
            })
    
    return result 