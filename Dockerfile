# Use an official Python runtime as the base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /adhdo_app

# Install any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Define environment variable for Flask to run in production mode
ENV FLASK_APP=adhdo.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run adhdo.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
