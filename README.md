# SayYes.ai Wedding Planner Chatbot API

A V0-compatible HTTP endpoint for the SayYes.ai wedding planner chatbot. This API is designed to be integrated with the landing page at sayyes.ai.

## Features

- Natural language conversation with a friendly wedding planner AI
- Specialized knowledge about wedding venues, dresses, hairstyles, and more
- Support for showing image carousels based on user queries
- Tracking of user interactions to guide the conversation flow
- Integration with Vercel Blob Storage for high-quality wedding images

## Deployment Instructions

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)
- Vercel Blob Storage account (for image hosting)

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
   VERCEL_PROJECT_ID=your_project_id  # Optional, defaults to "sayyes"
   ```
5. Run the server:
   ```
   python app.py
   ```

### Image Management

The application uses Vercel Blob Storage to host wedding images. The images are organized by category:

- Wedding venues
- Wedding dresses
- Wedding hairstyles
- Wedding cakes

Each image has associated metadata including title, description, location (for venues), price, and tags.

The image URLs follow the format:
```
https://{project_id}.blob.vercel-storage.com/{folder}/{filename}
```

Where:
- `project_id` is your Vercel project ID (defaults to "sayyes" if not specified)
- `folder` is the category folder (e.g., "wedding venues", "wedding dresses")
- `filename` is the name of the image file

## API Endpoints

### POST /api/chat

Handles chat requests from the landing page. Supports two formats:

1. Simple format:
```json
{
    "message": "User message here",
    "session_id": "unique-session-id"  // Optional
}
```

2. OpenAI-compatible format:
```json
{
    "messages": [
        {"role": "user", "content": "User message here"},
        {"role": "assistant", "content": "Previous assistant response"} // Optional
    ],
    "session_id": "unique-session-id"  // Optional
}
```

Response format:
```json
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
        "title": "Top Wedding Venues",
        "items": [
            {
                "image": "https://sayyes.blob.vercel-storage.com/wedding%20venues/image-name.png",
                "title": "Venue Name",
                "description": "Description of the venue",
                "location": "Location",
                "price": "$$",
                "tags": ["Tag1", "Tag2"]
            }
        ]
    }  // Optional, only included when action is show_carousel
}
```

### GET /api/health

Health check endpoint.

### GET /

Simple homepage.