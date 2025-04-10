from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph
from typing import Dict, List, Optional, Any
import json
import os
import asyncio
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.schema import FunctionMessage
from crawl_tools import get_images_from_url, get_local_images
from langchain.prompts import ChatPromptTemplate
from crawl4ai import crawl

# Load environment variables from .env file
load_dotenv()

@tool
def scrape_and_return(query: str) -> str:
    """
    Scrapes the web using a given query and returns structured results.
    
    Args:
        query: URL or search query to crawl
        
    Returns:
        Structured results from crawling the web
    """
    result = crawl(query)  # You can pass a URL or search query
    return result

# === Setup ===
llm = ChatOpenAI(
    model="gpt-4", 
    temperature=0.7,
    openai_api_key=os.environ.get("OPENAI_API_KEY")
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
    # Normalize category
    category = category.lower()
    
    # Define crawling URLs based on category and style
    crawl_urls = {
        "venues": f"https://www.weddingwire.com/c/{location.replace(' ', '-') if location else 'us'}/wedding-venues/11-vendors.html",
        "dresses": "https://www.davidsbridal.com/wedding-dresses",
        "hairstyles": "https://www.brides.com/gallery/wedding-hairstyle-ideas",
        "cakes": "https://www.weddingwire.com/wedding-ideas/wedding-cake-pictures"
    }
    
    # First try to get images from the web
    images = []
    if category in crawl_urls:
        try:
            # Run the async crawling function
            crawled_urls = asyncio.run(get_images_from_url(crawl_urls[category]))
            
            # Process the crawled URLs to match our expected format
            if category == "venues":
                images = [
                    {
                        "image": url,
                        "title": f"Venue {i+1}",
                        "description": f"Beautiful {style or 'elegant'} wedding venue" + (f" in {location}" if location else ""),
                        "location": location if location else "Various locations",
                        "price": "$$$" if i % 3 == 0 else ("$$" if i % 3 == 1 else "$"),
                        "tags": [style.title() if style else "Elegant", "Venue", "Wedding"]
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
            elif category == "dresses":
                images = [
                    {
                        "image": url,
                        "title": f"Designer Dress {i+1}",
                        "description": f"{style or 'Elegant'} wedding dress",
                        "designer": "Designer Collection",
                        "price": "$$$" if i % 3 == 0 else ("$$" if i % 3 == 1 else "$"),
                        "tags": [style.title() if style else "Elegant", "Dress", "Wedding"]
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
            elif category == "hairstyles":
                images = [
                    {
                        "image": url,
                        "title": f"Hairstyle {i+1}",
                        "description": f"{style or 'Beautiful'} wedding hairstyle",
                        "tags": [style.title() if style else "Elegant", "Hairstyle", "Wedding"]
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
            else:
                images = [
                    {
                        "image": url,
                        "title": f"{category.title()} {i+1}",
                        "description": f"{style or 'Stunning'} {category} inspiration",
                        "tags": [style.title() if style else "Elegant", category.title(), "Wedding"]
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
        except Exception as e:
            print(f"Error crawling for {category}: {e}")
            # Will fall back to local images
    
    # If no images were found via crawling or there was an error, use local fallbacks
    if not images:
        images = get_local_images(category)
        
        # Convert to new format if needed
        if images and "url" in images[0]:
            if category == "venues":
                images = [
                    {
                        "image": img.get("url"),
                        "title": img.get("name", "Beautiful Venue"),
                        "description": img.get("description", "Wedding venue"),
                        "location": location if location else "Various locations",
                        "price": "$$$" if i % 3 == 0 else ("$$" if i % 3 == 1 else "$"),
                        "tags": [style.title() if style else "Elegant", "Venue", "Wedding"]
                    } for i, img in enumerate(images)
                ]
            elif category == "dresses":
                images = [
                    {
                        "image": img.get("url"),
                        "title": f"Designer Dress {i+1}",
                        "description": img.get("description", "Wedding dress"),
                        "designer": img.get("designer", "Designer Collection"),
                        "price": "$$$" if i % 3 == 0 else ("$$" if i % 3 == 1 else "$"),
                        "tags": [style.title() if style else "Elegant", "Dress", "Wedding"]
                    } for i, img in enumerate(images)
                ]
            elif category == "hairstyles":
                images = [
                    {
                        "image": img.get("url"),
                        "title": f"Hairstyle {i+1}",
                        "description": img.get("description", "Wedding hairstyle"),
                        "tags": [style.title() if style else "Elegant", "Hairstyle", "Wedding"]
                    } for i, img in enumerate(images)
                ]
            else:
                images = [
                    {
                        "image": img.get("url"),
                        "title": f"{category.title()} {i+1}",
                        "description": img.get("description", f"{category} inspiration"),
                        "tags": [style.title() if style else "Elegant", category.title(), "Wedding"]
                    } for i, img in enumerate(images)
                ]
    
    # If we still have no images, use the mock data as final fallback
    if not images:
        # Create mock data in the new format
        mock_images = {
            "venues": [
                {
                    "image": "https://example.com/venue1.jpg",
                    "title": "The Grand Hall",
                    "description": f"Beautiful {style or 'elegant'} wedding venue" + (f" in {location}" if location else ""),
                    "location": location if location else "Various locations",
                    "price": "$$$",
                    "tags": [style.title() if style else "Elegant", "Indoor", "Luxury"]
                },
                {
                    "image": "https://example.com/venue2.jpg", 
                    "title": "Riverside Gardens",
                    "description": f"Stunning {style or 'modern'} wedding space" + (f" in {location}" if location else ""),
                    "location": location if location else "Various locations",
                    "price": "$$",
                    "tags": [style.title() if style else "Modern", "Garden", "Outdoor"]
                },
                {
                    "image": "https://example.com/venue3.jpg",
                    "title": "Hillside Vineyard",
                    "description": f"Charming {style or 'rustic'} wedding location" + (f" in {location}" if location else ""),
                    "location": location if location else "Various locations",
                    "price": "$$",
                    "tags": [style.title() if style else "Rustic", "Vineyard", "Outdoor"]
                }
            ],
            "dresses": [
                {
                    "image": "https://example.com/dress1.jpg",
                    "title": "Lace Elegance",
                    "description": f"{style or 'Elegant'} wedding dress with lace details",
                    "designer": "Vera Wang",
                    "price": "$$$",
                    "tags": [style.title() if style else "Elegant", "Lace", "Traditional"]
                },
                {
                    "image": "https://example.com/dress2.jpg",
                    "title": "Royal Train",
                    "description": f"{style or 'Classic'} wedding gown with long train",
                    "designer": "Pronovias",
                    "price": "$$$",
                    "tags": [style.title() if style else "Classic", "Train", "Formal"]
                },
                {
                    "image": "https://example.com/dress3.jpg",
                    "title": "Minimalist Beauty",
                    "description": f"{style or 'Modern'} minimalist wedding dress",
                    "designer": "Stella McCartney",
                    "price": "$$",
                    "tags": [style.title() if style else "Modern", "Minimalist", "Sleek"]
                }
            ],
            "hairstyles": [
                {
                    "image": "https://example.com/hair1.jpg",
                    "title": "Floral Updo",
                    "description": f"{style or 'Elegant'} updo with floral accents",
                    "tags": [style.title() if style else "Elegant", "Updo", "Floral"]
                },
                {
                    "image": "https://example.com/hair2.jpg",
                    "title": "Romantic Waves",
                    "description": f"{style or 'Romantic'} loose waves with side braid",
                    "tags": [style.title() if style else "Romantic", "Waves", "Braid"]
                },
                {
                    "image": "https://example.com/hair3.jpg",
                    "title": "Classic Chignon",
                    "description": f"{style or 'Classic'} sleek chignon with veil",
                    "tags": [style.title() if style else "Classic", "Chignon", "Veil"]
                }
            ],
            "cakes": [
                {
                    "image": "https://example.com/cake1.jpg",
                    "title": "Three-Tier Elegance",
                    "description": f"{style or 'Elegant'} three-tier wedding cake",
                    "price": "$$$",
                    "tags": [style.title() if style else "Elegant", "Three-Tier", "Traditional"]
                },
                {
                    "image": "https://example.com/cake2.jpg",
                    "title": "Geometric Modern",
                    "description": f"{style or 'Modern'} geometric design cake",
                    "price": "$$",
                    "tags": [style.title() if style else "Modern", "Geometric", "Artistic"]
                },
                {
                    "image": "https://example.com/cake3.jpg",
                    "title": "Rustic Naked Cake",
                    "description": f"{style or 'Rustic'} naked cake with fresh flowers",
                    "price": "$",
                    "tags": [style.title() if style else "Rustic", "Naked", "Floral"]
                }
            ]
        }
        images = mock_images.get(category, [])
    
    # Filter by style if provided
    if style and images:
        style = style.lower()
        filtered_images = [img for img in images if style in img.get("description", "").lower()]
        # If we have results after filtering, use them, otherwise use the original list
        if filtered_images:
            images = filtered_images
    
    # Filter by location if provided (primarily for venues)
    if location and category == "venues":
        location = location.lower()
        filtered_images = [img for img in images if location in img.get("description", "").lower() or location in img.get("location", "").lower()]
        # If we have results after filtering, use them, otherwise use the original list
        if filtered_images:
            images = filtered_images
    
    return json.dumps(images)

# Create the agent with function calling
tools = [get_wedding_images, scrape_and_return]

# === Agent Node Function ===
def agent_step(state: Dict) -> Dict:
    messages: List = state.get("messages", [])

    # Setup system tone
    system_prompt = """
    You are Snatcha, a fun, warm, and helpful AI wedding planning assistant.
    Keep responses short, friendly, and use emojis where appropriate.
    Respond like you're helping a close friend, but stay focused on the task.
    Only suggest things when asked — be clever, not pushy.
    
    You have access to show wedding images.
    Use the get_wedding_images tool to show relevant wedding inspiration images.
    
    You can also scrape the web for information.
    Use the scrape_and_return tool when you need to find information online.
    """

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
    
    # Create response message (regular or with function call results)
    response = AIMessage(content=reply_text)
    
    # Update seen flags based on what user is asking about
    last_input = messages[-1].content.lower() if messages else ""
    seen_venues = state.get("seen_venues", False)
    seen_dresses = state.get("seen_dresses", False)
    seen_hairstyles = state.get("seen_hairstyles", False)
    cta_shown = state.get("cta_shown", False)
    soft_cta_shown = state.get("soft_cta_shown", False)
    
    # Track what image types were requested in this interaction
    image_request = None
    carousel_type = None
    carousel_title = None
    
    # Basic keyword matching (for now — could replace w/ function call tools later)
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
        return {
            "messages": messages + [response],
            "text": "🥳 Looks like you're getting into the fun stuff! Want to see what a fully planned wedding experience feels like?",
            "suggested_action": "soft_cta",
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": True,
            "cta_shown": cta_shown,
        }

    if all([seen_venues, seen_dresses, seen_hairstyles]) and not cta_shown:
        return {
            "messages": messages + [response],
            "text": "🤖 Agent: I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨",
            "suggested_action": "cta",
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": soft_cta_shown,
            "cta_shown": True,
        }

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
                    # If the location is followed by additional words (like "in austin texas"), include them
                    if i+2 < len(words) and words[i+2] not in location_keywords:
                        location += " " + words[i+2]
                    break
        
        # Determine style from user input, if any
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

    # Regular response output
    output = {
        "messages": messages + [response],
        "text": reply_text,
        "seen_venues": seen_venues,
        "seen_dresses": seen_dresses,
        "seen_hairstyles": seen_hairstyles,
        "cta_shown": cta_shown,
        "soft_cta_shown": soft_cta_shown,
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

prompt = ChatPromptTemplate.from_messages([
    ("system", "You're a helpful AI wedding planner. Answer user questions with friendliness and clarity. You can show wedding images with get_wedding_images tool and search the web with scrape_and_return tool."),
    ("human", "{input}")
])

def create_openai_functions_agent(tools, prompt):
    llm = ChatOpenAI(temperature=0.7, model="gpt-4")
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        agent_kwargs={"system_message": prompt}
    )
    
    # Create a wrapper that implements the expected interface
    class AgentWrapper:
        def invoke(self, state):
            messages = state.get("messages", [])
            last_message = messages[-1].content if messages else ""
            
            try:
                # Call the agent with the input
                result = agent_executor.invoke({"input": last_message})
                reply = result.get("output", "I couldn't process that request.")
                
                # Create basic response structure
                response = {
                    "messages": messages,
                    "text": reply,
                    "seen_venues": state.get("seen_venues", False),
                    "seen_dresses": state.get("seen_dresses", False),
                    "seen_hairstyles": state.get("seen_hairstyles", False),
                    "cta_shown": state.get("cta_shown", False),
                    "soft_cta_shown": state.get("soft_cta_shown", False),
                }
                
                # Extract information for special handling
                last_input = last_message.lower()
                
                # Basic keyword matching
                if "venue" in last_input:
                    response["seen_venues"] = True
                    carousel_title = "Top Wedding Venues"
                    carousel_items = []
                    
                    # Try to get venue images
                    try:
                        carousel_items = json.loads(get_wedding_images("venues"))
                        response["carousel"] = {
                            "title": carousel_title,
                            "items": carousel_items
                        }
                    except Exception as e:
                        print(f"Error getting venue images: {e}")
                    
                elif "dress" in last_input:
                    response["seen_dresses"] = True
                    carousel_title = "Wedding Dress Collection"
                    carousel_items = []
                    
                    # Try to get dress images
                    try:
                        carousel_items = json.loads(get_wedding_images("dresses"))
                        response["carousel"] = {
                            "title": carousel_title,
                            "items": carousel_items
                        }
                    except Exception as e:
                        print(f"Error getting dress images: {e}")
                    
                elif "hairstyle" in last_input or "hair" in last_input:
                    response["seen_hairstyles"] = True
                    carousel_title = "Wedding Hairstyles"
                    carousel_items = []
                    
                    # Try to get hairstyle images
                    try:
                        carousel_items = json.loads(get_wedding_images("hairstyles"))
                        response["carousel"] = {
                            "title": carousel_title,
                            "items": carousel_items
                        }
                    except Exception as e:
                        print(f"Error getting hairstyle images: {e}")
                    
                elif "cake" in last_input:
                    carousel_title = "Wedding Cakes"
                    carousel_items = []
                    
                    # Try to get cake images
                    try:
                        carousel_items = json.loads(get_wedding_images("cakes"))
                        response["carousel"] = {
                            "title": carousel_title,
                            "items": carousel_items
                        }
                    except Exception as e:
                        print(f"Error getting cake images: {e}")
                
                return response
            except Exception as e:
                print(f"Error in agent: {e}")
                return {
                    "messages": messages,
                    "text": "Sorry, I couldn't process that request.",
                    "seen_venues": state.get("seen_venues", False),
                    "seen_dresses": state.get("seen_dresses", False),
                    "seen_hairstyles": state.get("seen_hairstyles", False),
                    "cta_shown": state.get("cta_shown", False),
                    "soft_cta_shown": state.get("soft_cta_shown", False),
                }
    
    return AgentWrapper()

sayyes_agent = create_openai_functions_agent(tools, prompt)