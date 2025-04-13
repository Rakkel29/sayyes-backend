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
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.memory import ConversationBufferMemory
from tavily import TavilyClient
from image_utils import get_images_by_category, get_images_from_url, get_local_images, scrape_and_return

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
    guest_count: Optional[int]
    budget: Optional[str]
    food_preferences: Optional[str]
    special_requests: Optional[str]
    planning_stage: str  # 'initial', 'collecting_info', 'sneak_peek', 'exploring', 'final_cta'
    info_collected: int  # Count of information items collected
    seen_venues: bool
    seen_dresses: bool
    seen_hairstyles: bool
    cta_shown: bool
    soft_cta_shown: bool
    email_collected: bool

# === Tools ===
@tool
def get_wedding_images(category: str) -> Dict[str, Any]:
    """
    Get wedding images by category.
    
    Args:
        category: The category to filter by (venues, dresses, hairstyles)
        
    Returns:
        Dictionary containing carousel data in the format:
        {
            "text": "Some intro text...",
            "carousel": {
                "title": "Section Title",
                "items": [
                    {
                        "image": "image_url",
                        "title": "item title",
                        "location": "location text",
                        "price": "$$",
                        "tags": ["tag1", "tag2"],
                        "share_url": "url"
                    }
                ]
            }
        }
    """
    try:
        # Get images from database or fallback
        images = list_images_by_category(category)
        
        if not images:
            return {
                "text": f"I couldn't find any {category} to show you right now.",
                "carousel": {
                    "title": f"{category.title()} Gallery",
                    "items": []
                }
            }
        
        # Format as carousel with the exact structure required by frontend
        return {
            "text": f"Here are some beautiful {category} for your special day! ✨",
            "carousel": {
                "title": f"{category.title()} Gallery",
                "items": [
                    {
                        "image": image["url"],
                        "title": image["title"],
                        "location": image.get("location", ""),
                        "price": image.get("price", ""),
                        "tags": image.get("tags", []),
                        "share_url": image["url"]  # Using the image URL as share URL
                    }
                    for image in images
                ]
            }
        }
    except Exception as e:
        print(f"Error getting wedding images: {e}")
        return {
            "text": "I encountered an error while fetching the images.",
            "carousel": {
                "title": "Error",
                "items": []
            }
        }

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
    
    # Get the current planning stage
    planning_stage = state.get("planning_stage", "initial")
    
    # If we're in the final CTA stage and email is collected, stop
    if planning_stage == "final_cta" and state.get("email_collected", False):
        return False
    
    # If we're in the final CTA stage and user wants to continue exploring, move to exploring stage
    if planning_stage == "final_cta":
        last_message = messages[-1].content.lower()
        if "continue exploring" in last_message or "show me more" in last_message:
            state["planning_stage"] = "exploring"
            return True
        return False
    
    # If we're in the exploring stage, continue
    if planning_stage == "exploring":
        return True
    
    # If we're in the sneak peek stage, continue
    if planning_stage == "sneak_peek":
        return True
    
    # If we're in the collecting info stage, continue
    if planning_stage == "collecting_info":
        return True
    
    # If this is the first message, continue
    if len(messages) == 1:
        return True
    
    # Check for sneak peek triggers
    last_message = messages[-1].content.lower()
    if any(phrase in last_message for phrase in ["love it", "show me more", "not that one"]):
        return True
    
    # If we've shown all categories and the CTA, stop
    if (state.get("seen_venues") and state.get("seen_dresses") and state.get("seen_hairstyles")) and state.get("cta_shown"):
        return False
    
    # Otherwise stop
    return False

def agent_node(state: AgentState) -> AgentState:
    """Process the current state and generate a response."""
    messages = state.get("messages", [])
    chat_history = state.get("chat_history", [])
    planning_stage = state.get("planning_stage", "initial")
    info_collected = state.get("info_collected", 0)

    # Setup system message with planning stage context
    system_message = SystemMessage(content=f"""
    You are Snatcha, a fun, warm, and helpful AI wedding planning assistant.
    Keep responses short, friendly, and use emojis where appropriate.
    Respond like you're helping a close friend, but stay focused on the task.
    
    You have access to:
    1. Show wedding images using the get_wedding_images tool
    2. Search the web using tavily_search
    3. Scrape and analyze web content using the scrape_and_return tool
    
    Current Planning Stage: {planning_stage}
    
    Wedding Planning Information Collected:
    - Style: {state.get("style_preference") or "Not specified"}
    - Location: {state.get("location_preference") or "Not specified"}
    - Guest Count: {state.get("guest_count") or "Not specified"}
    - Budget: {state.get("budget") or "Not specified"}
    - Food Preferences: {state.get("food_preferences") or "Not specified"}
    - Special Requests: {state.get("special_requests") or "Not specified"}
    
    Instructions based on planning stage:
    
    1. If in "initial" stage:
       - Greet the user warmly
       - Ask about their wedding theme/style (modern, rustic, boho, etc.)
       - Be conversational and friendly
    
    2. If in "collecting_info" stage:
       - Ask ONE question at a time about their wedding preferences
       - Focus on gathering: location, guest count, budget, food preferences, special requests
       - After collecting 2-3 pieces of information, move to "sneak_peek" stage
    
    3. If in "sneak_peek" stage:
       - Show a sneak peek of what you can do for their dream day
       - Use the get_wedding_images tool to show venues, dresses, and hairstyles
       - After showing images, move to "exploring" stage
    
    4. If in "exploring" stage:
       - Offer a soft CTA: "Would you like to keep exploring more options or dive into planning?"
       - Provide buttons: "Continue Planning" and "Show Me More"
       - If user wants to continue planning, move to "final_cta" stage
    
    5. If in "final_cta" stage:
       - Present the final CTA: "I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨"
       - Provide buttons: "Join the Waitlist" and "Continue Exploring"
       - If user wants to join waitlist, ask for their email
       - If user wants to continue exploring, move back to "exploring" stage
    
    When showing images:
    - Always use the get_wedding_images tool
    - Format your response as a JSON with "text" and "carousel" fields
    - The carousel should have a title and items with image, title, description, etc.
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
    
    # Process the response based on planning stage
    if messages:
        last_input = messages[-1].content.lower()
        
        # Extract information from user input
        if planning_stage == "initial":
            # Check for style preference
            style_keywords = ["modern", "rustic", "boho", "bohemian", "classic", "elegant", "traditional", "contemporary", "vintage"]
            for keyword in style_keywords:
                if keyword in last_input:
                    new_state["style_preference"] = keyword
                    new_state["planning_stage"] = "collecting_info"
                    new_state["info_collected"] += 1
                    break
        
        elif planning_stage == "collecting_info":
            # Check for location preference
            if "location" in last_input or "where" in last_input or "place" in last_input:
                # Extract location from the message
                location = last_input.split("in ")[-1].strip() if "in " in last_input else None
                if location:
                    new_state["location_preference"] = location
                    new_state["info_collected"] += 1
            
            # Check for guest count
            elif "guest" in last_input or "people" in last_input or "attend" in last_input:
                # Try to extract a number
                import re
                numbers = re.findall(r'\d+', last_input)
                if numbers:
                    new_state["guest_count"] = int(numbers[0])
                    new_state["info_collected"] += 1
            
            # Check for budget
            elif "budget" in last_input or "cost" in last_input or "spend" in last_input:
                # Extract budget information
                budget_keywords = ["small", "moderate", "large", "luxury", "affordable", "expensive"]
                for keyword in budget_keywords:
                    if keyword in last_input:
                        new_state["budget"] = keyword
                        new_state["info_collected"] += 1
                        break
            
            # Check for food preferences
            elif "food" in last_input or "catering" in last_input or "menu" in last_input or "dinner" in last_input:
                new_state["food_preferences"] = last_input
                new_state["info_collected"] += 1
            
            # Check for special requests
            elif "special" in last_input or "request" in last_input or "tradition" in last_input or "custom" in last_input:
                new_state["special_requests"] = last_input
                new_state["info_collected"] += 1
            
            # If we've collected enough information, move to sneak peek stage
            if new_state["info_collected"] >= 2:
                new_state["planning_stage"] = "sneak_peek"
        
        elif planning_stage == "sneak_peek":
            # Show a sneak peek of venues, dresses, and hairstyles
            if not new_state.get("seen_venues"):
                new_state["seen_venues"] = True
                function_message = FunctionMessage(
                    content=json.dumps({
                        "text": "Let me show you a sneak peek of what I can do for your dream day ✨",
                        "carousel": {
                            "title": "Beautiful Wedding Venues",
                            "items": []  # Will be populated by the tool
                        }
                    }),
                    name="get_wedding_images",
                    additional_kwargs={"category": "venues"}
                )
                new_chat_history.append(function_message)
            
            elif not new_state.get("seen_dresses"):
                new_state["seen_dresses"] = True
                function_message = FunctionMessage(
                    content=json.dumps({
                        "text": "Here are some stunning wedding dresses that might match your style!",
                        "carousel": {
                            "title": "Elegant Wedding Dresses",
                            "items": []  # Will be populated by the tool
                        }
                    }),
                    name="get_wedding_images",
                    additional_kwargs={"category": "dresses"}
                )
                new_chat_history.append(function_message)
            
            elif not new_state.get("seen_hairstyles"):
                new_state["seen_hairstyles"] = True
                function_message = FunctionMessage(
                    content=json.dumps({
                        "text": "And here are some beautiful hairstyles to complete your look!",
                        "carousel": {
                            "title": "Stunning Wedding Hairstyles",
                            "items": []  # Will be populated by the tool
                        }
                    }),
                    name="get_wedding_images",
                    additional_kwargs={"category": "hairstyles"}
                )
                new_chat_history.append(function_message)
                new_state["planning_stage"] = "exploring"
        
        elif planning_stage == "exploring":
            # Check if user wants to continue planning
            if "continue planning" in last_input or "dive into planning" in last_input:
                new_state["planning_stage"] = "final_cta"
                new_state["soft_cta_shown"] = True
        
        elif planning_stage == "final_cta":
            # Check if user wants to join the waitlist
            if "join" in last_input or "waitlist" in last_input:
                # Ask for email
                email_message = AIMessage(content="Great! Please provide your email address to join our exclusive wedding planning community.")
                new_chat_history.append(email_message)
            
            # Check if email was provided
            elif "@" in last_input and "." in last_input:
                new_state["email_collected"] = True
                email_confirmation = AIMessage(content="Thank you for joining our wedding planning community! We'll be in touch soon with exclusive planning tips and resources.")
                new_chat_history.append(email_confirmation)
    
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
    # Debug logging
    print(f"[Debug] Incoming message: {message}")
    print(f"[Debug] Initial state keys: {list(state.keys()) if state else 'None'}")
    
    # Initialize or use provided state
    if state is None:
        state = {
            "messages": [],
            "chat_history": [],
            "style_preference": None,
            "location_preference": None,
            "guest_count": None,
            "budget": None,
            "food_preferences": None,
            "special_requests": None,
            "planning_stage": "initial",
            "info_collected": 0,
            "seen_venues": False,
            "seen_dresses": False,
            "seen_hairstyles": False,
            "cta_shown": False,
            "soft_cta_shown": False,
            "email_collected": False
        }
    
    # Add the new message
    state["messages"].append(HumanMessage(content=message))
    
    # Create and run the graph
    graph = create_graph()
    
    # Handle recursion manually
    max_iterations = 10
    current_state = state
    for _ in range(max_iterations):
        try:
            # Run one iteration
            new_state = graph.invoke(current_state)
            
            # Check if we should continue
            if not should_continue(new_state):
                final_state = new_state
                break
                
            current_state = new_state
            current_state["messages"] = []  # Clear messages for next iteration
            
        except Exception as e:
            print(f"Error in graph iteration: {e}")
            final_state = current_state
            break
    else:
        # If we hit max iterations, use the last state
        final_state = current_state
    
    # Get the last message from chat history
    last_message = final_state["chat_history"][-1]
    
    # Prepare the response based on planning stage
    planning_stage = final_state.get("planning_stage", "initial")
    
    # If we're in the exploring stage and haven't shown the soft CTA yet
    if planning_stage == "exploring" and not final_state.get("soft_cta_shown"):
        # Update state to mark soft CTA as shown
        final_state["soft_cta_shown"] = True
        
        # Prepare the soft CTA response
        response = {
            "text": "Would you like to keep exploring more options or dive into planning?",
            "buttons": ["Continue Planning", "Show Me More"],
            "state": final_state
        }
    # If we're in the final CTA stage and haven't shown the CTA yet
    elif planning_stage == "final_cta" and not final_state.get("cta_shown"):
        # Update state to mark CTA as shown
        final_state["cta_shown"] = True
        
        # Prepare the CTA response
        response = {
            "text": "I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨",
            "buttons": ["Join the Waitlist", "Continue Exploring"],
            "state": final_state
        }
    # If we're asking for email
    elif planning_stage == "final_cta" and final_state.get("cta_shown") and not final_state.get("email_collected"):
        response = {
            "text": last_message.content,
            "state": final_state
        }
    # If email was collected
    elif final_state.get("email_collected"):
        response = {
            "text": last_message.content,
            "state": final_state
        }
    # Default response
    else:
        response = {
            "text": last_message.content,
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
        "guest_count": None,
        "budget": None,
        "food_preferences": None,
        "special_requests": None,
        "planning_stage": "initial",
        "info_collected": 0,
        "seen_venues": False,
        "seen_dresses": False,
        "seen_hairstyles": False,
        "cta_shown": False,
        "soft_cta_shown": False,
        "email_collected": False,
        "style_preference": None,
        "location_preference": None
    }
    
    while True:
        user_input = input("\n🤵 You: ")
        if user_input.lower() == 'quit':
            break
            
        response = process_message(user_input, state)
        print(f"\n👰 Snatcha: {response['text']}")
        state = response['state']
