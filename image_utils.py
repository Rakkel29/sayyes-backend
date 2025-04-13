import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote
from typing import List, Dict, Optional
import json
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

def clean_title(name: str) -> str:
    """Clean and format a title from a filename."""
    return name.split("/")[-1].replace("_", " ").split(".")[0].title()

def clean_description(description: str) -> str:
    """
    Clean and standardize a description string.
    
    Args:
        description: The description string to clean
        
    Returns:
        Cleaned description string
    """
    # Convert to string and strip whitespace
    description = str(description).strip()
    
    # Remove any duplicate descriptions that might be separated by newlines or semicolons
    if "\n" in description:
        description = description.split("\n")[0].strip()
    if ";" in description:
        description = description.split(";")[0].strip()
    
    return description

def list_venue_images() -> List[Dict]:
    """Get a list of venue images with their metadata."""
    filenames = [
        "eventsbomb_09464_A_very_elegant_and_luxurious.png",
        "amadeowang99_French_modern_wedding.png",
        "amadeowang99_Luxury_wedding_venue.png",
        "amadeowang99_Rustic_wedding_venue.png",
        "amadeowang99_Modern_wedding_venue.png"
    ]
    folder = "wedding venues"
    images = [
        {
            "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.public.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
            "title": clean_title(filename),
            "description": "Elegant wedding venue in Austin",
            "location": "Austin, TX",
            "price": "$$",
            "tags": ["Garden", "Outdoor"],
        }
        for filename in filenames
    ]
    return images

def list_dress_images() -> List[Dict]:
    """Get a list of dress images with their metadata."""
    filenames = [
        "alexb_79_Classic_Wedding_Dress.png",
        "amadeowang99_Modern_Wedding_Dress.png",
        "amadeowang99_Luxury_Wedding_Dress.png",
        "amadeowang99_Rustic_Wedding_Dress.png",
        "amadeowang99_Bohemian_Wedding_Dress.png"
    ]
    folder = "wedding dresses"
    return [
        {
            "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.public.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
            "title": clean_title(filename),
            "description": "Beautiful wedding dress",
            "designer": "Designer Collection",
            "price": "$$$",
            "tags": ["Dress", "Wedding"],
        }
        for filename in filenames
    ]

def list_hairstyle_images() -> List[Dict]:
    """Get a list of hairstyle images with their metadata."""
    filenames = [
        "alexb_79_Classic_Wedding_Hairstyle.png",
        "amadeowang99_Modern_Wedding_Hairstyle.png",
        "amadeowang99_Luxury_Wedding_Hairstyle.png",
        "amadeowang99_Rustic_Wedding_Hairstyle.png",
        "amadeowang99_Bohemian_Wedding_Hairstyle.png"
    ]
    folder = "wedding hairstyles"
    return [
        {
            "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.public.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
            "title": clean_title(filename),
            "description": "Stunning wedding hairstyle",
            "tags": ["Hairstyle", "Wedding"],
        }
        for filename in filenames
    ]

def list_cake_images() -> List[Dict]:
    """Get a list of cake images with their metadata."""
    filenames = [
        "alexb_79_Classic_Wedding_Cake.png",
        "amadeowang99_Modern_Wedding_Cake.png",
        "amadeowang99_Luxury_Wedding_Cake.png",
        "amadeowang99_Rustic_Wedding_Cake.png",
        "amadeowang99_Bohemian_Wedding_Cake.png"
    ]
    folder = "wedding cakes"
    return [
        {
            "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.public.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
            "title": clean_title(filename),
            "description": "Delicious wedding cake",
            "price": "$$$",
            "tags": ["Cake", "Wedding"],
        }
        for filename in filenames
    ]

def get_images_by_category(category: str, style: Optional[str] = None, location: Optional[str] = None) -> Dict:
    """
    Get wedding images for a specific category with optional style and location filters.
    
    Args:
        category: Type of images (venues, dresses, hairstyles, cakes, etc.)
        style: Optional style descriptor (rustic, modern, bohemian, etc.)
        location: Optional location specification
        
    Returns:
        Dictionary containing image data and carousel information
    """
    # Map category to the appropriate list function
    category_map = {
        "venues": list_venue_images,
        "dresses": list_dress_images,
        "hairstyles": list_hairstyle_images,
        "cakes": list_cake_images
    }
    
    # Get the appropriate list function
    list_function = category_map.get(category.lower())
    if not list_function:
        return {
            "text": f"I couldn't find any images for the category: {category}",
            "carousel": {
                "title": f"{category.title()} Collection",
                "items": []
            }
        }
    
    # Get the images
    items = list_function()
    
    # Filter by style if provided
    if style:
        items = [item for item in items if style.lower() in [tag.lower() for tag in item.get("tags", [])]]
    
    # Filter by location if provided
    if location:
        items = [item for item in items if location.lower() in item.get("location", "").lower()]
    
    # Format the response
    return {
        "text": f"Here are some {style if style else ''} {category} {f'in {location}' if location else ''}!",
        "carousel": {
            "title": f"{category.title()} Collection",
            "items": items
        }
    }

def get_images_from_url(url: str) -> List[str]:
    """
    Extract image URLs from a webpage.
    
    Args:
        url: The URL of the webpage to scrape
        
    Returns:
        List of image URLs found on the page
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all image tags
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, src)
                images.append(absolute_url)
        
        return images
    except Exception as e:
        print(f"Error fetching images from URL: {e}")
        return []

def get_local_images(directory: str) -> List[str]:
    """
    Get a list of image files from a local directory.
    
    Args:
        directory: Path to the directory containing images
        
    Returns:
        List of image file paths
    """
    try:
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        images = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    images.append(os.path.join(root, file))
        
        return images
    except Exception as e:
        print(f"Error getting local images: {e}")
        return []

def scrape_and_return(url: str) -> str:
    """
    Scrape content from a URL and return formatted text.
    
    Args:
        url: The URL to scrape
        
    Returns:
        Formatted text content from the webpage
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Convert HTML to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        markdown = h.handle(response.text)
        
        return markdown
    except Exception as e:
        print(f"Error scraping URL: {e}")
        return f"Error scraping content from {url}: {str(e)}"

def list_images_by_category(category: str) -> List[Dict[str, str]]:
    """
    List images by category from the database or fallback to blob storage.
    
    Args:
        category: The category to filter by (venues, dresses, hairstyles)
        
    Returns:
        List of dictionaries containing image data in the format:
        {
            "url": "image_url",
            "title": "item title",
            "location": "location text",
            "price": "$$",
            "tags": ["tag1", "tag2"]
        }
    """
    try:
        # Try to connect to the database first
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query images by category
        cursor.execute("""
            SELECT id, title, description, url, category, location, price, tags
            FROM images
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT 10
        """, (category,))
        
        # Fetch results
        rows = cursor.fetchall()
        
        # Format results
        images = []
        for row in rows:
            images.append({
                "url": row[3],
                "title": row[1],
                "location": row[5] or "",
                "price": row[6] or "",
                "tags": json.loads(row[7]) if row[7] else []
            })
        
        # If we got images from the database, return them
        if images:
            return images
            
    except Exception as e:
        print(f"Error listing images by category from database: {e}")
    
    # If database connection failed or no images found, fallback to blob storage
    try:
        # Map category to the appropriate list function
        category_map = {
            "venues": list_venue_images,
            "dresses": list_dress_images,
            "hairstyles": list_hairstyle_images,
            "cakes": list_cake_images
        }
        
        # Get the appropriate list function
        list_function = category_map.get(category.lower())
        if not list_function:
            print(f"No fallback images available for category: {category}")
            return []
        
        # Get the images from blob storage
        blob_images = list_function()
        
        # Convert to the expected format
        images = []
        for img in blob_images:
            images.append({
                "url": img["image"],
                "title": img["title"],
                "location": img.get("location", ""),
                "price": img.get("price", ""),
                "tags": img.get("tags", [])
            })
        
        return images
    except Exception as e:
        print(f"Error listing fallback images by category: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close() 