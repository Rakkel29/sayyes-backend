import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from additional_tests import LandingPageChatbot
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the chatbot
chatbot = LandingPageChatbot()

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle chat requests from the landing page.
    
    Supports two formats:
    
    1. Simple format:
    {
        "message": "User message here",
        "session_id": "unique-session-id"  // Optional
    }
    
    2. OpenAI-compatible format:
    {
        "messages": [
            {"role": "user", "content": "User message here"},
            {"role": "assistant", "content": "Previous assistant response"} // Optional
        ],
        "session_id": "unique-session-id"  // Optional
    }
    
    Response format:
    {
        "text": "Agent's response",
        "action": "text_only|show_carousel|cta|soft_cta",
        "user_info": {
            "seen_venues": bool,
            "seen_dresses": bool,
            "seen_hairstyles": bool,
            "cta_shown": bool,
            "soft_cta_shown": bool
        },
        "carousel": {
            "type": "venues|dresses|hairstyles|cakes",
            "items": [...]
        }  // Optional, only included when action is show_carousel
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    # Extract the message from either format
    user_message = None
    
    if "message" in data:
        # Simple format
        user_message = data["message"]
    elif "messages" in data and isinstance(data["messages"], list) and len(data["messages"]) > 0:
        # OpenAI-compatible format, get the last user message
        for msg in reversed(data["messages"]):
            if msg.get("role") == "user" and "content" in msg:
                user_message = msg["content"]
                break
    
    if not user_message:
        return jsonify({"error": "Missing message parameter or no valid user message in messages array"}), 400
    
    # Process the message using our chatbot
    response = chatbot.process_message(user_message)
    
    return jsonify(response)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def home():
    """Simple homepage."""
    return """
    <html>
    <head><title>SayYes.ai Wedding Planner Chatbot API</title></head>
    <body>
        <h1>SayYes.ai Wedding Planner Chatbot API</h1>
        <p>Use the /api/chat endpoint to interact with the chatbot.</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Get port from environment variable or use 8080 as default
    port = int(os.environ.get('PORT', 8080))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False) 