# Use an official Python image as the base
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy only requirements first to leverage Docker caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run the bot (adjust if your bot requires specific startup commands)
CMD ["python", "main.py"]