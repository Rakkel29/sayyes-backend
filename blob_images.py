import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote

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

def get_images_by_category(category: str, style: str = None, location: str = None):
    """Get images for a specific category with optional style and location filters"""
    category = category.lower()
    
    # Get the appropriate image list based on category
    if category == "venues":
        images = list_venue_images()
        # Apply location filter if provided
        if location:
            for img in images:
                img["location"] = location
                img["description"] = f"Beautiful wedding venue in {location}"
    elif category == "dresses":
        images = list_dress_images()
    elif category == "hairstyles":
        images = list_hairstyle_images()
    elif category == "cakes":
        images = list_cake_images()
    else:
        return []
    
    # Apply style filter if provided
    if style:
        style = style.lower()
        for img in images:
            if style in ["rustic", "modern", "bohemian", "luxury", "classic"]:
                img["title"] = f"{style.title()} {img['title']}"
                img["tags"].append(style.title())
    
    return images 