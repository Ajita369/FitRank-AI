# Use an official, lightweight Python runtime
FROM python:3.10-slim

# Set environment variables to prevent Python from writing pyc files and to buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for compiling certain native packages if required)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to prevent downloading large CUDA libraries
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements file first to utilize Docker layer caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Ensure output directory exists inside the container
RUN mkdir -p /app/output

# Run pytest on build/startup to ensure environment is fully correct
RUN python -m pytest

# Set default command to execute the ranking pipeline
CMD ["python", "rank.py", "--candidates", "data/candidates.jsonl", "--out", "output/submission.csv"]
