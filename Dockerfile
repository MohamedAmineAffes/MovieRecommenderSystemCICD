FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
COPY cleaned_file.py .
COPY script_stage.py .
COPY recommender.py .
COPY *.csv .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK corpora
RUN python -m nltk.downloader stopwords wordnet

# Run the application
CMD ["python", "cleaned_file.py"]