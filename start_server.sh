#!/bin/bash

# Exit on error
set -e

# Print environment info
echo "Python version:"
python --version

echo "Current directory:"
pwd

# Activate virtual environment if present
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Export environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the Flask server
echo "Starting server..."
python app.py 