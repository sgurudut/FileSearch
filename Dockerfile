# Use official Python image from Docker Hub as a base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /FileSearchApp/FileSearch

# Copy the requirements.txt file into the container
COPY requirements_test_env.txt .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements_test_env.txt

# Copy the entire application into the container
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "fast_api_test:app", "--host", "0.0.0.0", "--port", "8000"]
