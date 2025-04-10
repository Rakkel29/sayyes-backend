import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please update the .env file with your actual API key.")
    exit(1)

# Initialize the OpenAI client
client = OpenAI()

try:
    # Simple test query
    query = "What are some popular wedding themes for summer?"
    
    print(f"\n=== Testing query: '{query}' ===")
    
    # Make a simple completion request
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful wedding planning assistant named Snatcha."},
            {"role": "user", "content": query}
        ]
    )
    
    # Print the response
    print("\nResponse from OpenAI API:")
    print(response.choices[0].message.content)
    
    print("\nAPI connection is working!")
    
except Exception as e:
    print(f"Error testing OpenAI API: {e}") 