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

# Load environment variables from .env file
load_dotenv()

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
                        "url": url,
                        "description": f"Beautiful {style or 'elegant'} wedding venue" + (f" in {location}" if location else ""),
                        "name": f"Venue {i+1}"
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
            elif category == "dresses":
                images = [
                    {
                        "url": url,
                        "description": f"{style or 'Elegant'} wedding dress",
                        "designer": "Designer Collection"
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
            elif category == "hairstyles":
                images = [
                    {
                        "url": url,
                        "description": f"{style or 'Beautiful'} wedding hairstyle"
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
            else:
                images = [
                    {
                        "url": url,
                        "description": f"{style or 'Stunning'} {category} inspiration"
                    } for i, url in enumerate(crawled_urls[:5])  # Limit to 5 images
                ]
        except Exception as e:
            print(f"Error crawling for {category}: {e}")
            # Will fall back to local images
    
    # If no images were found via crawling or there was an error, use local fallbacks
    if not images:
        images = get_local_images(category)
    
    # If we still have no images, use the mock data as final fallback
    if not images:
        # Fallback to mock data
        mock_images = {
            "venues": [
                {
                    "url": "https://example.com/venue1.jpg",
                    "description": f"Beautiful {style or 'elegant'} wedding venue" + (f" in {location}" if location else ""),
                    "name": "The Grand Hall"
                },
                {
                    "url": "https://example.com/venue2.jpg", 
                    "description": f"Stunning {style or 'modern'} wedding space" + (f" in {location}" if location else ""),
                    "name": "Riverside Gardens"
                },
                {
                    "url": "https://example.com/venue3.jpg",
                    "description": f"Charming {style or 'rustic'} wedding location" + (f" in {location}" if location else ""),
                    "name": "Hillside Vineyard"
                }
            ],
            "dresses": [
                {
                    "url": "https://example.com/dress1.jpg",
                    "description": f"{style or 'Elegant'} wedding dress with lace details",
                    "designer": "Vera Wang"
                },
                {
                    "url": "https://example.com/dress2.jpg",
                    "description": f"{style or 'Classic'} wedding gown with long train",
                    "designer": "Pronovias"
                },
                {
                    "url": "https://example.com/dress3.jpg",
                    "description": f"{style or 'Modern'} minimalist wedding dress",
                    "designer": "Stella McCartney"
                }
            ],
            "hairstyles": [
                {
                    "url": "https://example.com/hair1.jpg",
                    "description": f"{style or 'Elegant'} updo with floral accents"
                },
                {
                    "url": "https://example.com/hair2.jpg",
                    "description": f"{style or 'Romantic'} loose waves with side braid"
                },
                {
                    "url": "https://example.com/hair3.jpg",
                    "description": f"{style or 'Classic'} sleek chignon with veil"
                }
            ],
            "cakes": [
                {
                    "url": "https://example.com/cake1.jpg",
                    "description": f"{style or 'Elegant'} three-tier wedding cake"
                },
                {
                    "url": "https://example.com/cake2.jpg",
                    "description": f"{style or 'Modern'} geometric design cake"
                },
                {
                    "url": "https://example.com/cake3.jpg",
                    "description": f"{style or 'Rustic'} naked cake with fresh flowers"
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
        filtered_images = [img for img in images if location in img.get("description", "").lower()]
        # If we have results after filtering, use them, otherwise use the original list
        if filtered_images:
            images = filtered_images
    
    return json.dumps(images)

# Create the agent with function calling
tools = [get_wedding_images]

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
    suggested_action = "text_only"
    
    # Basic keyword matching (for now — could replace w/ function call tools later)
    if "venue" in last_input:
        seen_venues = True
        image_request = "venues"
        suggested_action = "show_carousel"
        carousel_type = "venues"
    elif "dress" in last_input:
        seen_dresses = True
        image_request = "dresses"
        suggested_action = "show_carousel"
        carousel_type = "dresses"
    elif "hairstyle" in last_input or "hair" in last_input:
        seen_hairstyles = True
        image_request = "hairstyles"
        suggested_action = "show_carousel"
        carousel_type = "hairstyles"
    elif "cake" in last_input:
        image_request = "cakes"
        suggested_action = "show_carousel"
        carousel_type = "cakes"
    else:
        carousel_type = None

    # CTA logic (soft prompt after 2 categories, full CTA after all 3)
    categories_seen = sum([seen_venues, seen_dresses, seen_hairstyles])

    if categories_seen >= 2 and not soft_cta_shown:
        return {
            "messages": messages + [response],
            "reply": "🥳 Looks like you're getting into the fun stuff! Want to see what a fully planned wedding experience feels like?",
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
            "reply": "🤖 Agent: I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨",
            "suggested_action": "cta",
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": soft_cta_shown,
            "cta_shown": True,
        }

    # If there's an image request, get the images
    image_results = None
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
            image_results = json.loads(get_wedding_images(image_request, style, location))
        except Exception as e:
            print(f"Error getting images: {e}")
            image_results = []

    # Regular response output
    output = {
        "messages": messages + [response],
        "reply": reply_text,
        "suggested_action": suggested_action,
        "carousel_type": carousel_type,
        "seen_venues": seen_venues,
        "seen_dresses": seen_dresses,
        "seen_hairstyles": seen_hairstyles,
        "cta_shown": cta_shown,
        "soft_cta_shown": soft_cta_shown,
    }
    
    # Add image results to output if available
    if image_results:
        output["carousel_items"] = image_results

    return output

# === LangGraph Graph Setup ===
graph = StateGraph(dict)
graph.add_node("agent", agent_step)
graph.set_entry_point("agent")
graph.set_finish_point("agent")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You're a helpful AI wedding planner. Answer user questions with friendliness and clarity."),
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
                    "reply": reply,
                    "suggested_action": "text_only",
                    "carousel_type": None,
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
                    response["suggested_action"] = "show_carousel"
                    response["carousel_type"] = "venues"
                elif "dress" in last_input:
                    response["seen_dresses"] = True
                    response["suggested_action"] = "show_carousel"
                    response["carousel_type"] = "dresses"
                elif "hairstyle" in last_input or "hair" in last_input:
                    response["seen_hairstyles"] = True
                    response["suggested_action"] = "show_carousel"
                    response["carousel_type"] = "hairstyles"
                elif "cake" in last_input:
                    response["suggested_action"] = "show_carousel"
                    response["carousel_type"] = "cakes"
                
                return response
            except Exception as e:
                print(f"Error in agent: {e}")
                return {
                    "messages": messages,
                    "reply": "Sorry, I couldn't process that request.",
                    "suggested_action": "text_only",
                    "carousel_type": None,
                    "seen_venues": state.get("seen_venues", False),
                    "seen_dresses": state.get("seen_dresses", False),
                    "seen_hairstyles": state.get("seen_hairstyles", False),
                    "cta_shown": state.get("cta_shown", False),
                    "soft_cta_shown": state.get("soft_cta_shown", False),
                }
    
    return AgentWrapper()

sayyes_agent = create_openai_functions_agent(tools, prompt)