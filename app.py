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
        if not messages or not isinstance(messages, list) or not isinstance(messages[-1], dict):
            return jsonify({"error": "Invalid message format"}), 400

        message = messages[-1].get("content")
        if not message or not isinstance(message, str):
            return jsonify({"error": "Message content missing or invalid"}), 400

        state = data.get("state", None)
        
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