# *********************************************************************
#
#  _     _____ ____ ___ _  _____  _   _ __________
# | |   | ____|  _ \_ _| |/ / _ \| | | |__  / ____|
# | |   |  _| | |_) | || ' / | | | | | | / /|  _|
# | |___| |___|  __/| || . \ |_| | |_| |/ /_| |___
# |_____|_____|_|  |___|_|\_\___/ \___//____|_____|
#
#  -------------------------------------------------------------------
#                         BAKCUP-PORTAINER-GITHUB
#          https://github.com/lepikouze/backup-portainer-github
#  -------------------------------------------------------------------
#
# Automated backup of Docker stacks and environment files from Portainer to a GitHub repository.
#
# Base image with Python 3.9
FROM python:3.9-slim

# PROVIDE IMAGE LABLES
LABEL "com.example.vendor"="ACME Incorporated"
LABEL version="1.0"
LABEL org.opencontainers.image.title="backup-portainer-github"
LABEL org.opencontainers.image.source="https://github.com/lepikouze/backup-portainer-github"
LABEL description="Automated backup of Docker stacks and environment files from Portainer to a GitHub repository."
LABEL maintainer="Lepikouze"
LABEL org.opencontainers.image.licenses="MIT"

# Install required packages
RUN apt-get update && apt-get install -y git

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create Woring directory
RUN mkdir -p /app

# Copy the application code
COPY app.py /app

# Set working directory
WORKDIR /app

# Set exe file
RUN chmod +x /app/app.py

# Set the entrypoint to run the Flask app
CMD ["python", "app.py"]
