from bs4 import BeautifulSoup
import os
import glob
from urllib.parse import quote
from typing import List, Dict
import json
import requests

def get_images_from_url(url: str) -> list:
    """Mock function that returns a list of image URLs from a webpage."""
    return [
        {"url": "https://example.com/image1.jpg", "alt": "Wedding Venue 1"},
        {"url": "https://example.com/image2.jpg", "alt": "Wedding Venue 2"}
    ]

def get_local_images(directory: str) -> List[Dict]:
    """
    Get images from a local directory.
    
    Args:
        directory: The directory to search for images
        
    Returns:
        List of dictionaries containing image information
    """
    # In a real implementation, this would scan a local directory
    # For now, return sample data
    return [
        {
            "url": "local/path/to/image1.jpg",
            "title": "Local Image 1",
            "description": "A beautiful local image"
        }
    ]

def get_local_images(category: str) -> list:
    """Mock function that returns a list of local image paths."""
    return [
        f"/images/{category}/image1.jpg",
        f"/images/{category}/image2.jpg"
    ]

def get_local_images(category: str) -> list[dict]:
    """
    Get local fallback images for a specific category.
    
    Args:
        category: Type of images (venues, dresses, hairstyles)
        
    Returns:
        List of dictionaries with image information
    """
    # Map categories to their proper blob storage folder names
    folder_map = {
        'venues': 'wedding venues',
        'dresses': 'wedding dresses',
        'hairstyles': 'hairstyles',
        'cakes': 'wedding cakes'
    }
    
    # Get the proper folder name for the category
    folder = folder_map.get(category, category)
    
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
                "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
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
                "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
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
                "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
                "title": title,
                "description": description,
                "tags": ["Elegant", "Hairstyle", "Wedding"]
            })
        else:
            # Generic format for other categories
            title = f"{category.title()} {i+1}"
            description = f"{name.title()} for weddings"
            result.append({
                "image": f"https://{os.getenv('VERCEL_PROJECT_ID')}.blob.vercel-storage.com/{quote(folder)}/{quote(filename)}",
                "title": title,
                "description": description,
                "tags": ["Wedding", category.title()]
            })
    
    return result 