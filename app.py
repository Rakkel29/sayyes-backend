import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import logging
from langchain_core.messages import HumanMessage
from sayyes_agent import process_message  # import the process_message function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get port from environment variable or default to 8080
port = int(os.environ.get('PORT', 8080))

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle chat requests from the landing page.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        logger.info(f"Received chat request: {data}")
        
        # Extract message and state from request
        messages = data.get("messages", [])
        
        # Enhanced validation for messages
        if not messages:
            logger.warning("Empty messages array received")
            return jsonify({"error": "No messages provided"}), 400
            
        if not isinstance(messages, list):
            logger.warning(f"Messages is not a list: {type(messages)}")
            return jsonify({"error": "Messages must be a list"}), 400
            
        if not messages:
            logger.warning("Messages list is empty")
            return jsonify({"error": "Messages list is empty"}), 400
            
        if not isinstance(messages[-1], dict):
            logger.warning(f"Last message is not a dict: {type(messages[-1])}")
            return jsonify({"error": "Last message must be a dictionary"}), 400

        message = messages[-1].get("content")
        
        # Enhanced validation for message content
        if message is None:
            logger.warning("Message content is None")
            return jsonify({"error": "Message content is missing"}), 400
            
        if not isinstance(message, str):
            logger.warning(f"Message content is not a string: {type(message)}")
            # Convert to string if possible, otherwise use empty string
            try:
                message = str(message)
                logger.info(f"Converted message to string: {message}")
            except Exception as e:
                logger.error(f"Failed to convert message to string: {e}")
                message = ""
                logger.info("Using empty string as fallback")

        state = data.get("state", None)
        
        # Debug logging
        logger.info(f"[DEBUG] Extracted message: {message}")
        logger.info(f"[DEBUG] Extracted state: {state}")
        
        # Process the message
        result = process_message(message, state)
        
        # Return the result
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com"""
    return jsonify({
        "status": "healthy",
        "chat_available": True
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        "status": "SayYes Agent API is running",
        "chat_available": True,
        "environment": "production"
    }), 200

if __name__ == '__main__':
    logger.info(f"Starting server on port {port}")
    logger.info("Chat functionality: ENABLED (production mode)")
    app.run(host='0.0.0.0', port=port) 