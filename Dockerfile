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
# Base image with Python 3.9-Alpine
FROM python:3.9-alpine

# PROVIDE IMAGE LABLES
LABEL maintainer="Lepikouze"
LABEL org.opencontainers.image.title="backup-portainer-github"
LABEL org.opencontainers.image.source="https://github.com/lepikouze/backup-portainer-github"
LABEL description="Automated backup of Docker stacks and environment files from Portainer to a GitHub repository."
LABEL org.opencontainers.image.licenses="MIT"


# Install only essential system packages
RUN apk add --no-cache git gcc musl-dev libffi-dev

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
