import os
from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.tools import Tool
import json
from blob_images import get_images_by_category

# Load environment variables
load_dotenv()

# Define wedding planner system prompt
WEDDING_PLANNER_PROMPT = """
You are Snatcha, a fun and friendly AI-powered wedding planner. 
You help users choose wedding venues, dresses, hairstyles, and planning tips 
while being supportive, playful, and stylish ✨💍🎉
"""

# Define simple tools
def get_wedding_images(category, style=None, location=None):
    """
    Get wedding images for a specific category.
    
    Args:
        category: Type of images (venues, dresses, hairstyles, cakes, etc.)
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

# Create tools
tools = [
    Tool(
        name="GetWeddingImages",
        func=get_wedding_images,
        description="Get wedding images for a specific category like venues, dresses, hairstyles, or cakes. You can specify style and location."
    )
]

# Initialize ChatOpenAI
llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

# Create the agent
agent_executor = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Define a Cursor-compatible interface
class LandingPageChatbot:
    def __init__(self):
        self.conversation_history = []
        self.user_info = {
            "seen_venues": False,
            "seen_dresses": False,
            "seen_hairstyles": False,
            "cta_shown": False,
            "soft_cta_shown": False
        }
    
    def process_message(self, user_message):
        """
        Process a user message and return a response with UI action suggestions.
        
        Args:
            user_message: String containing the user's message
            
        Returns:
            dict: Response containing the agent's reply and UI action suggestions
        """
        # Add user message to conversation history
        self.conversation_history.append(HumanMessage(content=user_message))
        
        # Invoke the agent
        try:
            result = agent_executor.invoke({"input": user_message})
            reply_text = result["output"]
        except Exception as e:
            print(f"Error invoking agent: {e}")
            reply_text = "Sorry, I couldn't process your request right now."
        
        # Add AI response to conversation history
        self.conversation_history.append(AIMessage(content=reply_text))
        
        # Extract information for special handling
        last_input = user_message.lower()
        
        # Determine action and carousel type based on content
        action = "text_only"
        carousel_type = None
        carousel_items = None
        
        # Basic keyword matching
        if "venue" in last_input:
            self.user_info["seen_venues"] = True
            action = "show_carousel"
            carousel_type = "venues"
            carousel_items = json.loads(get_wedding_images("venues"))
        elif "dress" in last_input:
            self.user_info["seen_dresses"] = True
            action = "show_carousel"
            carousel_type = "dresses"
            carousel_items = json.loads(get_wedding_images("dresses"))
        elif "hairstyle" in last_input or "hair" in last_input:
            self.user_info["seen_hairstyles"] = True
            action = "show_carousel"
            carousel_type = "hairstyles"
            carousel_items = json.loads(get_wedding_images("hairstyles"))
        elif "cake" in last_input:
            action = "show_carousel"
            carousel_type = "cakes"
            carousel_items = json.loads(get_wedding_images("cakes"))
        
        # CTA logic (soft prompt after 2 categories, full CTA after all 3)
        categories_seen = sum([
            self.user_info["seen_venues"], 
            self.user_info["seen_dresses"], 
            self.user_info["seen_hairstyles"]
        ])
        
        if categories_seen >= 2 and not self.user_info["soft_cta_shown"]:
            self.user_info["soft_cta_shown"] = True
            action = "soft_cta"
            reply_text = "🥳 Looks like you're getting into the fun stuff! Want to see what a fully planned wedding experience feels like?"
        
        if all([self.user_info["seen_venues"], self.user_info["seen_dresses"], self.user_info["seen_hairstyles"]]) and not self.user_info["cta_shown"]:
            self.user_info["cta_shown"] = True
            action = "cta"
            reply_text = "🤖 I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level? Over 500 couples have already joined our exclusive wedding planning community! ✨"
        
        # Format the response
        response = {
            "text": reply_text,
            "action": action,
            "user_info": self.user_info,
            "is_typing": False
        }
        
        # Add carousel items if available
        if carousel_items:
            response["carousel"] = {
                "type": carousel_type,
                "items": carousel_items
            }
        
        return response

# Example usage
if __name__ == "__main__":
    chatbot = LandingPageChatbot()
    
    # Example conversation
    queries = [
        "Can you help me find a wedding venue?",
        "I'm looking for a wedding dress",
        "What hairstyles would look good with a veil?"
    ]
    
    for query in queries:
        print(f"\nUser: {query}")
        response = chatbot.process_message(query)
        print(f"Agent: {response['text']}")
        print(f"Suggested Action: {response['action']}")
        
        if "carousel" in response:
            print(f"Showing {response['carousel']['type']} carousel with {len(response['carousel']['items'])} items")
        
        print(f"User Info: {response['user_info']}") 