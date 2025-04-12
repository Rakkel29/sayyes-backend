# Use a slim Python 3.9 base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables (Render uses these)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose the port (Render uses 8080)
EXPOSE 8080

# Command to run the app
CMD ["python", "app.py"]
