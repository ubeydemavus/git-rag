# Use official Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install Git and other system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file
COPY requirements.txt /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port used by the FastAPI app
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"] 
