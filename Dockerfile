FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for PyTorch and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads document_data static/css static/js

# Make sure the app has access to the directories
RUN chmod -R 777 uploads document_data

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]