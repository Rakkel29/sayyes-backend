import os
from dotenv import load_dotenv
from sayyes_agent import sayyes_agent
from langchain.schema import HumanMessage

# Load environment variables from .env file if present
load_dotenv()

# Check if OpenAI API key is set
if not os.environ.get("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not set.")
    print("Please set your API key using: export OPENAI_API_KEY='your-api-key'")
    print("Or create a .env file with OPENAI_API_KEY=your-api-key")
    exit(1)

def test_agent(query):
    """Test the agent with a given query and print the results."""
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "seen_venues": False,
        "seen_dresses": False,
        "seen_hairstyles": False,
        "cta_shown": False,
        "soft_cta_shown": False,
    }

    print(f"\n=== Testing query: '{query}' ===")
    
    try:
        result = sayyes_agent.invoke(initial_state)
        
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
        
        return result
    except Exception as e:
        print(f"Error testing agent: {e}")
        return None

if __name__ == "__main__":
    # Test with various queries
    
    # Test venue search with location
    test_agent("Can you show me some rustic wedding venues in Austin?")
    
    # Test dress search
    test_agent("I'm looking for a modern wedding dress with minimalist design")
    
    # Test hairstyle search
    test_agent("What are some romantic wedding hairstyles for long hair?")
    
    # Test search functionality
    test_agent("What's the average cost of a wedding in New York?")
    
    # Test wedding cake options
    test_agent("Show me some elegant wedding cake designs")
    
    # Test a question that should just give text response
    test_agent("What should I consider when choosing a wedding date?") 