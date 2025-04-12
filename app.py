import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
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

        # Return test mode response
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

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com"""
    return jsonify({
        "status": "healthy",
        "chat_available": False
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        "status": "SayYes Agent API is running",
        "chat_available": False,
        "environment": "local testing"
    }), 200

if __name__ == '__main__':
    logger.info(f"Starting server on port {port}")
    logger.info("Chat functionality: DISABLED (local testing mode)")
    app.run(host='0.0.0.0', port=port) 