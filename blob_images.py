import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote
from typing import List, Dict, Optional
import json

# Load environment variables
load_dotenv()

def list_venue_images():
    # Hardcoded or fetched from a file/blob listing
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
    
    # Print each image URL for debugging
    for image in images:
        print("Returning image URL:", image["image"])
    
    return images

def list_dress_images():
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

def list_hairstyle_images():
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

def list_cake_images():
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

def clean_title(name: str):
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

def get_images_by_category(category: str, style: Optional[str] = None, location: Optional[str] = None) -> Dict:
    """
    Get wedding images for a specific category.
    
    Args:
        category: Type of images (venues, dresses, hairstyles, cakes, flowers, etc.)
        style: Optional style descriptor (rustic, modern, bohemian, etc.)
        location: Optional location specification
        
    Returns:
        Dictionary with text and carousel structure
    """
    # Try to get images from blob storage first
    try:
        if category == "venues":
            images = list_venue_images()
            title = "Wedding Venues"
        elif category == "dresses":
            images = list_dress_images()
            title = "Wedding Dress Collection"
        elif category == "hairstyles":
            images = list_hairstyle_images()
            title = "Wedding Hairstyles"
        elif category == "cakes":
            images = list_cake_images()
            title = "Wedding Cakes"
        else:
            images = []
            title = f"{category.title()} Collection"

        # If we got images from blob storage
        if images:
            # Clean descriptions for each image
            for image in images:
                if "description" in image:
                    image["description"] = clean_description(image["description"])
                # Add buttons to each image
                image["buttons"] = ["Love it", "Share", "Save"]
            
            # Filter by style if provided
            if style:
                images = [img for img in images if any(tag.lower() == style.lower() for tag in img.get("tags", []))]
            
            # Filter by location if provided (only for venues)
            if location and category == "venues":
                images = [img for img in images if location.lower() in img.get("location", "").lower()]
            
            # Return in the exact structure specified
            return {
                "text": f"Here's what I found for you!",
                "carousel": {
                    "title": title,
                    "items": images
                }
            }

    except Exception as e:
        print(f"Error getting images from blob storage: {e}")
        
    # If blob storage failed or returned no images, use sample data
    sample_images = {
        "venues": [
            {
                "image": "https://example.com/venue1.jpg",
                "title": "Elegant Garden Venue",
                "description": "Beautiful outdoor garden venue perfect for spring and summer weddings",
                "location": "Austin, TX",
                "price": "$$$",
                "tags": ["outdoor", "garden", "elegant"]
            },
            {
                "image": "https://example.com/venue2.jpg",
                "title": "Modern Downtown Loft",
                "description": "Contemporary urban venue with city views",
                "location": "Austin, TX",
                "price": "$$$$",
                "tags": ["modern", "urban", "indoor"]
            }
        ],
        "dresses": [
            {
                "image": "https://example.com/dress1.jpg",
                "title": "Classic A-Line Gown",
                "description": "Timeless elegance with a modern twist",
                "designer": "Designer Name",
                "price": "$$$",
                "tags": ["classic", "elegant", "a-line"]
            }
        ],
        "hairstyles": [
            {
                "image": "https://example.com/hair1.jpg",
                "title": "Romantic Updo",
                "description": "Soft, romantic updo with loose tendrils",
                "tags": ["updo", "romantic", "classic"]
            }
        ],
        "cakes": [
            {
                "image": "https://example.com/cake1.jpg",
                "title": "Three-Tier Buttercream",
                "description": "Classic three-tier cake with buttercream frosting",
                "tags": ["classic", "buttercream", "three-tier"]
            }
        ]
    }
    
    # Filter by category
    if category not in sample_images:
        return {
            "text": "I couldn't find any images for that category.",
            "carousel": {
                "title": f"{category.title()} Collection",
                "items": []
            }
        }
        
    images = sample_images[category]
    
    # Clean descriptions for each image
    for image in images:
        if "description" in image:
            image["description"] = clean_description(image["description"])
        # Add buttons to each image
        image["buttons"] = ["Love it", "Share", "Save"]
    
    # Filter by style if provided
    if style:
        images = [img for img in images if style.lower() in [tag.lower() for tag in img.get("tags", [])]]
    
    # Filter by location if provided (only for venues)
    if location and category == "venues":
        images = [img for img in images if location.lower() in img.get("location", "").lower()]
    
    # Return in the exact structure specified
    return {
        "text": f"Here's what I found for you!",
        "carousel": {
            "title": f"{category.title()} Collection",
            "items": images
        }
    } 