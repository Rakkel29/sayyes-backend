import os
import sys
import logging
from dotenv import load_dotenv
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SayYes-API")

# Load environment variables
load_dotenv()

def start_server():
    try:
        # Get port from environment variable or use 8080 as default
        port = int(os.environ.get('PORT', 8080))
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Starting SayYes.ai Wedding Planner API on {host}:{port}")
        
        # Check for OpenAI API key
        if not os.environ.get('OPENAI_API_KEY'):
            logger.warning("OPENAI_API_KEY not set! Please set it in your .env file or environment variables.")
        
        # Run the Flask app
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server() 