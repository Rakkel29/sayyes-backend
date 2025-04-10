# SayYes.ai Wedding Planner Chatbot API

A V0-compatible HTTP endpoint for the SayYes.ai wedding planner chatbot. This API is designed to be integrated with the landing page at sayyes.ai.

## Features

- Natural language conversation with a friendly wedding planner AI
- Specialized knowledge about wedding venues, dresses, hairstyles, and more
- Support for showing image carousels based on user queries
- Tracking of user interactions to guide the conversation flow

## Deployment Instructions

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Local Deployment

1. Clone this repository
2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up the environment variables:
   Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PORT=8080  # Optional, defaults to 8080
   ```
5. Run the server:
   ```