import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please update the .env file with your actual API key.")
    exit(1)

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4", 
    temperature=0.6,
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

# Define tools
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
    # Mock data based on the category
    images = {
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
                "description": f"{style or 'Elegant'} updo with floral accents" + (f" for {style} hair" if style else "")
            },
            {
                "url": "https://example.com/hair2.jpg",
                "description": f"{style or 'Romantic'} loose waves with side braid" + (f" for {style} hair" if style else "")
            },
            {
                "url": "https://example.com/hair3.jpg",
                "description": f"{style or 'Classic'} sleek chignon with veil" + (f" for {style} hair" if style else "")
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
    
    # Default to empty list if category not found
    category_images = images.get(category.lower(), [])
    
    # Filter by style if provided
    if style and category_images:
        style = style.lower()
        filtered_images = [img for img in category_images if style in img["description"].lower()]
        if filtered_images:
            category_images = filtered_images
    
    # Filter by location if provided (only for venues)
    if location and category.lower() == "venues":
        location = location.lower()
        filtered_images = [img for img in category_images if location in img["description"].lower()]
        if filtered_images:
            category_images = filtered_images
    
    return json.dumps(category_images)

# Create the agent
tools = [get_wedding_images]

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are Snatcha, a fun, warm, and helpful AI wedding planning assistant.
Keep responses short, friendly, and use emojis where appropriate.
Respond like you're helping a close friend, but stay focused on the task.
Only suggest things when asked — be clever, not pushy.

You have access to show wedding images.
Use the get_wedding_images tool to show relevant wedding inspiration images.
"""),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create agent executor
agent = AgentExecutor.from_agent_and_tools(
    agent=create_openai_functions_agent(llm, tools, prompt),
    tools=tools,
    verbose=True
)

# Test queries
test_queries = [
    "What are some affordable wedding venues in Miami?",
    "What's the average cost for a wedding DJ in Chicago?",
    "Best wedding hairstyles for short curly hair"
]

# Run tests
for query in test_queries:
    print(f"\n=== Testing query: '{query}' ===")
    
    try:
        # Execute the agent
        result = agent.invoke({"input": query})
        
        # Print the result
        print("\nResponse:")
        print(result["output"])
        
    except Exception as e:
        print(f"Error: {e}") 