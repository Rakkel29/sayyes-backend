#!/bin/bash

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Export environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Start the Flask server
python app.py 