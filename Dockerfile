FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
COPY recommender.py .
COPY app.py .           
COPY templates/ templates/
COPY models/ models/
COPY tests/ tests/


# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK corpora
RUN python -m nltk.downloader stopwords wordnet

# Expose Flask port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]