import os
from dotenv import load_dotenv
from sayyes_agent import sayyes_agent
from langchain_core.messages import HumanMessage

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please update the .env file with your actual API key.")
    exit(1)

# Custom query for testing
custom_query = "What's a good wedding theme for a summer beach wedding?"

# Setup initial state
initial_state = {
    "messages": [HumanMessage(content=custom_query)],
    "seen_venues": False,
    "seen_dresses": False,
    "seen_hairstyles": False,
    "cta_shown": False,
    "soft_cta_shown": False,
}

print(f"\n=== Testing query: '{custom_query}' ===")

try:
    # Invoke the agent
    result = sayyes_agent.invoke(initial_state)
    
    # Print the results
    print("\nReply:", result["reply"])
    print("\nSuggested Action:", result["suggested_action"])
    
    if result["suggested_action"] == "show_carousel":
        print("Carousel Type:", result["carousel_type"])
        
        if "carousel_items" in result:
            print("\nCarousel Items:")
            for i, item in enumerate(result["carousel_items"]):
                print(f"  Item {i+1}:")
                for key, value in item.items():
                    print(f"    {key}: {value}")
    
    # Print state changes for tracking
    state_changes = {
        "seen_venues": result["seen_venues"],
        "seen_dresses": result["seen_dresses"],
        "seen_hairstyles": result["seen_hairstyles"],
        "soft_cta_shown": result["soft_cta_shown"],
        "cta_shown": result["cta_shown"],
    }
    print("\nState Changes:", state_changes)

except Exception as e:
    print(f"Error testing agent: {e}") 