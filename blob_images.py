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

def get_images_by_category(category: str, style: str = None, location: str = None) -> dict:
    """Mock function that returns wedding images for a category."""
    return {
        "text": f"Here are some {style if style else ''} {category} {f'in {location}' if location else ''}!",
        "carousel": {
            "title": f"{category.title()} Collection",
            "items": [
                {
                    "image": f"/images/{category}/1.jpg",
                    "title": f"Beautiful {category.title()} 1",
                    "description": f"A stunning {style if style else ''} {category} option",
                    "location": location if location else "Various Locations",
                    "price": "$$$",
                    "buttons": ["Love it", "Share", "Save"],
                    "tags": [style] if style else []
                },
                {
                    "image": f"/images/{category}/2.jpg",
                    "title": f"Beautiful {category.title()} 2",
                    "description": f"Another gorgeous {style if style else ''} {category} choice",
                    "location": location if location else "Various Locations",
                    "price": "$$$$",
                    "buttons": ["Love it", "Share", "Save"],
                    "tags": [style] if style else []
                }
            ]
        }
    } 