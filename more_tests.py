import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_community.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
from typing import Optional
from blob_images import get_images_by_category

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