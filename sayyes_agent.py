from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph
from typing import Dict, List, Optional, Any
import json
import os
import asyncio
from dotenv import load_dotenv
from langchain_core.tools import tool, Tool
from langchain_community.agents import AgentExecutor, initialize_agent, AgentType
from langchain_core.messages import FunctionMessage
from crawl_tools import get_images_from_url, get_local_images
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from blob_images import get_images_by_category
from langchain_community.memory import ConversationBufferMemory
from langchain_community.tools import TavilySearchResults
from bs4 import BeautifulSoup
import requests
import html2text

# Load environment variables from .env file if it exists, otherwise use OS environment
load_dotenv(override=True)  # This will load .env if it exists but won't override existing OS environment variables

# Get API keys from environment (either from .env or OS environment)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
VERCEL_PROJECT_ID = os.environ.get("VERCEL_PROJECT_ID")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

if not VERCEL_PROJECT_ID:
    raise ValueError("VERCEL_PROJECT_ID environment variable is not set")

@tool
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
            search = TavilySearchResults(max_results=1)
            results = search.invoke(query)
            if not results:
                return json.dumps({"error": "No results found"})
            url = results[0].get('url')

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

# === Setup ===
llm = ChatOpenAI(
    model="gpt-4", 
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)

# === Tools ===
@tool
def get_wedding_images(category: str, style: Optional[str] = None, location: Optional[str] = None) -> str:
    """
    Get wedding images for a specific category.
    
    Args:
        category: Type of images (venues, dresses, hairstyles, cakes, flowers, etc.)
        style: Optional style descriptor (rustic, modern, bohemian, etc.)
        location: Optional location specification
        
    Returns:
        JSON string with image URLs and descriptions
    """
    try:
        # First try to get images from primary source
        images = get_images_by_category(category, style, location)
        
        # If no images found, use backup blob storage
        if not images:
            print(f"No images found in primary source, using backup from blob storage for {category}")
            images = get_images_by_category(category, style, location)
        
        return json.dumps(images)
    except Exception as e:
        print(f"Error fetching images: {e}, using backup from blob storage")
        # Use backup images from blob storage
        backup_images = get_images_by_category(category, style, location)
        return json.dumps(backup_images)

# Create the agent with function calling
tools = [
    get_wedding_images,
    scrape_and_return,
    TavilySearchResults(max_results=3)
]

# === Agent Node Function ===
def agent_step(state: Dict) -> Dict:
    messages: List = state.get("messages", [])
    chat_history: List = state.get("chat_history", [])

    # Setup system tone
    system_message = SystemMessage(content="""
    You are Snatcha, a fun, warm, and helpful AI wedding planning assistant.
    Keep responses short, friendly, and use emojis where appropriate.
    Respond like you're helping a close friend, but stay focused on the task.
    Only suggest things when asked — be clever, not pushy.
    
    You have access to:
    1. Show wedding images using the get_wedding_images tool
    2. Search the web using Tavily search
    3. Scrape and analyze web content using the scrape_and_return tool
    
    When users ask about wedding-related topics:
    - Use web search to find up-to-date information
    - Show relevant images when appropriate
    - Provide helpful, personalized advice
    - Keep the conversation engaging and friendly
    """)

    # Combine chat history with current message
    all_messages = [system_message] + chat_history + messages

    # Create agent executor for function calling
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True
    )
    
    # Get the user's latest message
    last_user_message = messages[-1].content if messages else ""
    
    # Execute agent with tools
    try:
        agent_response = agent.invoke({"input": last_user_message})
        reply_text = agent_response["output"]
    except Exception as e:
        print(f"Error invoking agent: {e}")
        reply_text = "Sorry, I couldn't process your request right now."
    
    # Create response message
    response_message = AIMessage(content=reply_text)
    
    # Update chat history
    new_chat_history = chat_history + messages + [response_message]
    
    # Update seen flags based on what user is asking about
    last_input = last_user_message.lower()
    seen_venues = state.get("seen_venues", False)
    seen_dresses = state.get("seen_dresses", False)
    seen_hairstyles = state.get("seen_hairstyles", False)
    cta_shown = state.get("cta_shown", False)
    soft_cta_shown = state.get("soft_cta_shown", False)
    
    # Track what image types were requested in this interaction
    image_request = None
    carousel_type = None
    carousel_title = None
    
    # Basic keyword matching
    if "venue" in last_input:
        seen_venues = True
        image_request = "venues"
        carousel_type = "venues"
        carousel_title = "Top Wedding Venues"
    elif "dress" in last_input:
        seen_dresses = True
        image_request = "dresses"
        carousel_type = "dresses"
        carousel_title = "Wedding Dress Collection"
    elif "hairstyle" in last_input or "hair" in last_input:
        seen_hairstyles = True
        image_request = "hairstyles"
        carousel_type = "hairstyles"
        carousel_title = "Wedding Hairstyles"
    elif "cake" in last_input:
        image_request = "cakes"
        carousel_type = "cakes"
        carousel_title = "Wedding Cakes"

    # CTA logic (soft prompt after 2 categories, full CTA after all 3)
    categories_seen = sum([seen_venues, seen_dresses, seen_hairstyles])

    if categories_seen >= 2 and not soft_cta_shown:
        output = {
            "text": "🥳 Looks like you're getting into the fun stuff! Want to see what a fully planned wedding experience feels like?",
            "chat_history": new_chat_history,
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": True,
            "cta_shown": cta_shown,
        }
        return output

    if all([seen_venues, seen_dresses, seen_hairstyles]) and not cta_shown:
        output = {
            "text": "🤖 I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨",
            "chat_history": new_chat_history,
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": soft_cta_shown,
            "cta_shown": True,
        }
        return output

    # If there's an image request, get the images
    carousel_items = None
    if image_request:
        # Extract location from input if available
        location = None
        if image_request == "venues":
            location_keywords = ["in", "at", "near", "around"]
            words = last_input.split()
            for i, word in enumerate(words):
                if word in location_keywords and i+1 < len(words):
                    location = words[i+1]
                    if i+2 < len(words) and words[i+2] not in location_keywords:
                        location += " " + words[i+2]
                    break
        
        # Determine style from user input
        style_keywords = {
            "rustic": ["rustic", "country", "barn", "outdoor"],
            "modern": ["modern", "contemporary", "minimalist", "sleek"],
            "elegant": ["elegant", "luxury", "upscale", "fancy"],
            "bohemian": ["bohemian", "boho", "relaxed", "free-spirited"],
            "vintage": ["vintage", "retro", "antique", "classic"],
            "romantic": ["romantic", "intimate", "dreamy"],
        }
        
        style = None
        for style_name, keywords in style_keywords.items():
            if any(keyword in last_input for keyword in keywords):
                style = style_name
                break
        
        try:
            carousel_items = json.loads(get_wedding_images(image_request, style, location))
        except Exception as e:
            print(f"Error getting images: {e}")
            carousel_items = []

    # Prepare output
    output = {
        "text": reply_text,
        "chat_history": new_chat_history,
        "seen_venues": seen_venues,
        "seen_dresses": seen_dresses,
        "seen_hairstyles": seen_hairstyles,
        "soft_cta_shown": soft_cta_shown,
        "cta_shown": cta_shown,
    }
    
    # Add carousel to output if available
    if carousel_items and carousel_title:
        output["carousel"] = {
            "title": carousel_title,
            "items": carousel_items
        }

    return output

# === LangGraph Graph Setup ===
graph = StateGraph(dict)
graph.add_node("agent", agent_step)
graph.set_entry_point("agent")
graph.set_finish_point("agent")

# Compile the graph
chain = graph.compile()

# Interactive command-line interface
if __name__ == "__main__":
    print("👰 Wedding Planning Assistant - Type 'quit' to exit")
    print("Ask me anything about wedding venues, dresses, hairstyles, or cakes!")
    
    # Initial state
    state = {
        "messages": [],
        "chat_history": [],
        "seen_venues": False,
        "seen_dresses": False,
        "seen_hairstyles": False,
        "cta_shown": False,
        "soft_cta_shown": False
    }
    
    while True:
        user_input = input("\n🤵 You: ")
        if user_input.lower() == 'quit':
            print("Goodbye! 👋")
            break
            
        # Add user message to state
        state["messages"] = [HumanMessage(content=user_input)]
        
        # Get response from agent
        response = chain.invoke(state)
        
        # Update state with response
        state = {
            "messages": [],  # Clear messages for next iteration
            "chat_history": response.get("chat_history", []),  # Keep chat history
            "seen_venues": response.get("seen_venues", False),
            "seen_dresses": response.get("seen_dresses", False),
            "seen_hairstyles": response.get("seen_hairstyles", False),
            "cta_shown": response.get("cta_shown", False),
            "soft_cta_shown": response.get("soft_cta_shown", False)
        }
        
        # Print the response
        print("\n👰 Assistant:", response.get("text", ""))
        
        # If there's a carousel, show the images
        if "carousel" in response:
            print(f"\n📸 {response['carousel']['title']}:")
            for item in response['carousel']['items']:
                print(f"- {item.get('description', 'No description')} ({item.get('url', 'No URL')})")