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
FROM python:3.9-slim-bookworm

# PROVIDE IMAGE LABLES
LABEL maintainer="Lepikouze"
LABEL org.opencontainers.image.title="backup-portainer-github"
LABEL org.opencontainers.image.source="https://github.com/lepikouze/backup-portainer-github"
LABEL description="Automated backup of Docker stacks and environment files from Portainer to a GitHub repository."
LABEL org.opencontainers.image.licenses="MIT"


# Install only essential system packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    git ca-certificates curl && \
    apt-get purge -y perl libldap-2.5-0 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
