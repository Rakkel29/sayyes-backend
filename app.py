import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from additional_tests import LandingPageChatbot
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the chatbot only if we have the required API keys
try:
    chatbot = LandingPageChatbot()
except Exception as e:
    logger.warning(f"Chatbot initialization skipped (this is normal for local testing): {str(e)}")
    chatbot = None

# Get port from environment variable or default to 8080
port = int(os.environ.get('PORT', 8080))

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
    try:
        if chatbot is None:
            return jsonify({
                "text": "Chat functionality is only available in production environment. Local testing mode active.",
                "action": "text_only",
                "user_info": {
                    "seen_venues": False,
                    "seen_dresses": False,
                    "seen_hairstyles": False,
                    "cta_shown": False,
                    "soft_cta_shown": False
                }
            }), 200

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        logger.info(f"Received chat request: {data}")

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
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com"""
    return jsonify({
        "status": "healthy",
        "chat_available": chatbot is not None
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        "status": "SayYes Agent API is running",
        "chat_available": chatbot is not None,
        "environment": "production" if chatbot is not None else "local testing"
    }), 200

if __name__ == '__main__':
    logger.info(f"Starting server on port {port}")
    logger.info(f"Chat functionality: {'ENABLED' if chatbot is not None else 'DISABLED (local testing mode)'}")
    app.run(host='0.0.0.0', port=port) 