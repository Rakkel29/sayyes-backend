import json
import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin
from tavily import TavilyClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

def scrape_and_return(query: str) -> str:
    """
    Scrapes the web using a given query and returns structured results.
    
    Args:
        query: URL or search query to crawl
        
    Returns:
        Structured results from crawling the web
    """
    try:
        # First try to get the URL directly if it's a URL
        if query.startswith(('http://', 'https://')):
            url = query
        else:
            # Use Tavily search to find relevant URLs
            search = TavilyClient(api_key=TAVILY_API_KEY).search(query, search_depth="advanced", max_results=1)
            if not search:
                return json.dumps({"error": "No results found"})
            url = search[0].get('url')

        # Fetch and parse the webpage
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            # Convert HTML to markdown for better readability
            h = html2text.HTML2Text()
            h.ignore_links = False
            content = h.handle(str(main_content))
        else:
            content = "No content found"
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                images.append({
                    'url': src,
                    'alt': alt
                })
        
        return json.dumps({
            "title": title,
            "content": content,
            "url": url,
            "images": images[:5]  # Limit to first 5 images
        })
    except Exception as e:
        return json.dumps({
            "error": f"Error scraping content: {str(e)}"
        }) 