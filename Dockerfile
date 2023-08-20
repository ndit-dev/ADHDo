# Use an official Python runtime as the base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /adhdo_app

# Install tzdata and any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt

# Install tzdata and Python requirements
RUN apt-get update && apt-get install -y tzdata && \
    pip install -r requirements.txt

# Setup timezone based on TZ environment variable
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy the current directory contents into the container at /app
COPY . .

# Define environment variable for Flask to run in production mode and the default timezone
ENV FLASK_APP=adhdo.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV TZ=Europe/Stockholm

# Run adhdo.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
