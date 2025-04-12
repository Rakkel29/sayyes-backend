from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, FunctionMessage
from langgraph.graph import StateGraph
from typing import Dict, List, Optional, Any, Sequence, TypedDict, Union, Tuple
import json
import os
import asyncio
from dotenv import load_dotenv
from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage
from crawl_tools import get_images_from_url, get_local_images
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from blob_images import get_images_by_category
from langchain.memory import ConversationBufferMemory
from tavily import TavilyClient
from bs4 import BeautifulSoup
import requests
import html2text
from urllib.parse import urljoin
from scrape_utils import scrape_and_return

# Load environment variables from .env file if it exists, otherwise use OS environment
load_dotenv(override=True)

# Get API keys from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
VERCEL_PROJECT_ID = os.environ.get("VERCEL_PROJECT_ID")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is not set")
if not VERCEL_PROJECT_ID:
    raise ValueError("VERCEL_PROJECT_ID environment variable is not set")

# Define state type
class AgentState(TypedDict):
    messages: List[BaseMessage]
    chat_history: List[BaseMessage]
    style_preference: Optional[str]
    location_preference: Optional[str]
    seen_venues: bool
    seen_dresses: bool
    seen_hairstyles: bool
    cta_shown: bool
    soft_cta_shown: bool

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
        # Get images from blob storage
        result = get_images_by_category(category, style, location)
        
        # Sanitize and standardize descriptions in carousel items
        if "carousel" in result and "items" in result["carousel"]:
            for item in result["carousel"]["items"]:
                # Ensure description is a string and not duplicated
                if "description" in item:
                    # Remove any HTML tags or special formatting
                    description = str(item["description"]).strip()
                    # Remove any duplicate descriptions that might be separated by newlines or semicolons
                    if "\n" in description:
                        description = description.split("\n")[0].strip()
                    if ";" in description:
                        description = description.split(";")[0].strip()
                    # Update the description
                    item["description"] = description
                
                # Ensure buttons are present
                if "buttons" not in item:
                    item["buttons"] = ["Love it", "Share", "Save"]
        
        # Return the sanitized result
        return json.dumps(result)
    except Exception as e:
        print(f"Error fetching images: {e}")
        # Return a fallback response with the correct structure
        return json.dumps({
            "text": "I couldn't find any images for that category.",
            "carousel": {
                "title": f"{category.title()} Collection",
                "items": []
            }
        })

@tool
def tavily_search(query: str) -> str:
    """
    Search the web using Tavily API.
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)
    search_result = client.search(query, search_depth="advanced", max_results=3)
    return json.dumps(search_result)

# === Setup LLM ===
llm = ChatOpenAI(
    model="gpt-4", 
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)

# === Agent Node Functions ===
def should_continue(state: AgentState) -> Union[Tuple[bool, str], bool]:
    """Determine if we should continue running the agent."""
    messages = state["messages"]
    if not messages:
        return False
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        return True
    return False

def agent_node(state: AgentState) -> AgentState:
    """Process the current state and generate a response."""
    messages = state.get("messages", [])
    chat_history = state.get("chat_history", [])

    # Setup system message
    system_message = SystemMessage(content=f"""
    You are Snatcha, a fun, warm, and helpful AI wedding planning assistant.
    Keep responses short, friendly, and use emojis where appropriate.
    Respond like you're helping a close friend, but stay focused on the task.
    Only suggest things when asked — be clever, not pushy.
    
    You have access to:
    1. Show wedding images using the get_wedding_images tool
    2. Search the web using tavily_search
    3. Scrape and analyze web content using the scrape_and_return tool
    
    When users ask about wedding-related topics:
    - Use web search to find up-to-date information
    - Show relevant images when appropriate
    - Provide helpful, personalized advice
    - Keep the conversation engaging and friendly
    
    User Preferences:
    {f'Style: {state.get("style_preference")}' if state.get("style_preference") else ''}
    {f'Location: {state.get("location_preference")}' if state.get("location_preference") else ''}
    """)

    # Combine messages for context
    all_messages = [system_message] + chat_history + messages

    # Get response from LLM
    response = llm.invoke(all_messages)
    
    # Update chat history
    new_chat_history = chat_history + messages + [response]
    
    # Update state
    new_state = state.copy()
    new_state["messages"] = []  # Clear messages
    new_state["chat_history"] = new_chat_history
    
    # Update tracking flags based on content
    if messages:
        last_input = messages[-1].content.lower()
        if any(word in last_input for word in ["venue", "location", "place", "where"]):
            new_state["seen_venues"] = True
        elif any(word in last_input for word in ["dress", "gown", "outfit"]):
            new_state["seen_dresses"] = True
        elif any(word in last_input for word in ["hair", "style", "hairstyle"]):
            new_state["seen_hairstyles"] = True
    
    return new_state

# === Graph Setup ===
def create_graph() -> StateGraph:
    """Create and configure the agent graph."""
    workflow = StateGraph(AgentState)
    
    # Add the agent node
    workflow.add_node("agent", agent_node)
    
    # Add edges
    workflow.add_edge("agent", "agent")
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    return workflow.compile()

# === Main Processing Function ===
def process_message(message: str, state: Optional[Dict] = None) -> Dict:
    """Process a message and return the response."""
    # Initialize or use provided state
    if state is None:
        state = {
            "messages": [],
            "chat_history": [],
            "style_preference": None,
            "location_preference": None,
            "seen_venues": False,
            "seen_dresses": False,
            "seen_hairstyles": False,
            "cta_shown": False,
            "soft_cta_shown": False
        }
    
    # Add the new message
    state["messages"].append(HumanMessage(content=message))
    
    # Create and run the graph
    graph = create_graph()
    final_state = graph.invoke(state)
    
    # Get the last message from chat history
    last_message = final_state["chat_history"][-1]
    
    # Prepare the response
    response = {
        "message": last_message.content,
        "state": final_state
    }
    
    return response

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
        "soft_cta_shown": False,
        "style_preference": None,
        "location_preference": None
    }
    
    while True:
        user_input = input("\n🤵 You: ")
        if user_input.lower() == 'quit':
            print("Goodbye! 👋")
            break
            
        # Process the message
        result = process_message(user_input, state)
        
        # Update state with response
        state = result["state"]
        
        # Print the response
        print("\n👰 Assistant:", result["message"])
        
        # If there's a carousel, show the images
        if "carousel" in result["state"]:
            print(f"\n📸 {result['state']['carousel']['title']}:")
            for item in result['state']['carousel']['items']:
                print(f"- {item.get('description', 'No description')} ({item.get('url', 'No URL')})")
