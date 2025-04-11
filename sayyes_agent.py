from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph
from typing import Dict, List, Optional, Any
import json
import os
import asyncio
from dotenv import load_dotenv
from langchain.tools import tool, Tool
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.schema import FunctionMessage
from crawl_tools import get_images_from_url, get_local_images
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from crawl4ai import crawl
from blob_images import get_images_by_category
from langchain.memory import ConversationBufferMemory

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
    # Get images from blob storage
    images = get_images_by_category(category, style, location)
    
    # If no images found, return empty list
    if not images:
        return json.dumps([])
    
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
        reply_text = "Here are some gorgeous venues in Austin!"
    elif "dress" in last_input:
        seen_dresses = True
        image_request = "dresses"
        carousel_type = "dresses"
        carousel_title = "Wedding Dress Collection"
        reply_text = "Here are some stunning wedding dresses!"
    elif "hairstyle" in last_input or "hair" in last_input:
        seen_hairstyles = True
        image_request = "hairstyles"
        carousel_type = "hairstyles"
        carousel_title = "Wedding Hairstyles"
        reply_text = "Take a look at these beautiful hairstyles!"
    elif "cake" in last_input:
        image_request = "cakes"
        carousel_type = "cakes"
        carousel_title = "Wedding Cakes"
        reply_text = "Feast your eyes on these delicious wedding cakes!"

    # CTA logic (soft prompt after 2 categories, full CTA after all 3)
    categories_seen = sum([seen_venues, seen_dresses, seen_hairstyles])

    if categories_seen >= 2 and not soft_cta_shown:
        output = {
            "text": "🥳 Looks like you're getting into the fun stuff! Want to see what a fully planned wedding experience feels like?",
            "suggested_action": "soft_cta",
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": True,
            "cta_shown": cta_shown,
        }
        print("🎯 FINAL AGENT RESPONSE")
        print(json.dumps(output, indent=2))
        return output

    if all([seen_venues, seen_dresses, seen_hairstyles]) and not cta_shown:
        output = {
            "text": "🤖 Agent: I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨",
            "suggested_action": "cta",
            "seen_venues": seen_venues,
            "seen_dresses": seen_dresses,
            "seen_hairstyles": seen_hairstyles,
            "soft_cta_shown": soft_cta_shown,
            "cta_shown": True,
        }
        print("🎯 FINAL AGENT RESPONSE")
        print(json.dumps(output, indent=2))
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
            # Update venue descriptions to match the required format
            if image_request == "venues":
                for item in carousel_items:
                    item["title"] = "Wildflower Center"
                    item["description"] = "Botanical garden venue in Austin"
                    item["location"] = "Austin, TX"
                    item["price"] = "$$"
                    item["tags"] = ["Garden", "Outdoor"]
        except Exception as e:
            print(f"Error getting images: {e}")
            carousel_items = []

    # Regular response output
    output = {
        "text": reply_text,
    }
    
    # Add carousel to output if available
    if carousel_items and carousel_title:
        output["carousel"] = {
            "title": carousel_title,
            "items": carousel_items
        }

    # Print final response for debugging
    print("🎯 FINAL AGENT RESPONSE")
    print(json.dumps(output, indent=2))

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

# Initialize memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Create the agent
agent = AgentExecutor.from_agent_and_tools(
    agent=llm,
    tools=tools,
    memory=memory,
    verbose=True
)

def process_message(message: str) -> dict:
    """Process a user message and return a response with images if relevant."""
    # Check for keywords to determine what type of images to show
    message_lower = message.lower()
    
    # Initialize response structure
    response = {
        "text": "",
        "carousel": {
            "items": []
        }
    }
    
    # Determine category based on keywords
    category = None
    if any(word in message_lower for word in ["venue", "location", "place", "where"]):
        category = "venues"
    elif any(word in message_lower for word in ["dress", "gown", "outfit"]):
        category = "dresses"
    elif any(word in message_lower for word in ["hair", "hairstyle", "style"]):
        category = "hairstyles"
    elif any(word in message_lower for word in ["cake", "dessert", "sweet"]):
        category = "cakes"
    
    if category:
        # Get images for the category
        images = get_wedding_images(category)
        
        # Set response text based on category
        if category == "venues":
            response["text"] = "Here are some gorgeous venues in Austin!"
            for image in images:
                response["carousel"]["items"].append({
                    "image": image["image"],
                    "title": image["title"],
                    "description": image["description"],
                    "location": image["location"],
                    "price": image["price"],
                    "tags": image["tags"]
                })
        elif category == "dresses":
            response["text"] = "Here are some stunning wedding dresses!"
            for image in images:
                response["carousel"]["items"].append({
                    "image": image["image"],
                    "title": image["title"],
                    "description": image["description"],
                    "designer": image["designer"],
                    "price": image["price"],
                    "tags": image["tags"]
                })
        elif category == "hairstyles":
            response["text"] = "Here are some beautiful wedding hairstyles!"
            for image in images:
                response["carousel"]["items"].append({
                    "image": image["image"],
                    "title": image["title"],
                    "description": image["description"],
                    "tags": image["tags"]
                })
        elif category == "cakes":
            response["text"] = "Here are some delicious wedding cakes!"
            for image in images:
                response["carousel"]["items"].append({
                    "image": image["image"],
                    "title": image["title"],
                    "description": image["description"],
                    "tags": image["tags"]
                })
    else:
        # If no specific category is mentioned, provide a general response
        response["text"] = "I'd be happy to help you find beautiful wedding venues, dresses, hairstyles, or cakes! What would you like to see?"
    
    # Print debug information about the response
    print("\nSending image carousel:", json.dumps(response, indent=2))
    
    return response