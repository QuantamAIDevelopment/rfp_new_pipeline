#!/bin/bash

# Azure App Service startup script for FastAPI application
echo "Starting RFP Processing Pipeline..."

# Install dependencies if not already installed
if [ ! -d "/home/site/wwwroot/venv" ]; then
    echo "Creating virtual environment..."
    python -m venv /home/site/wwwroot/venv
fi

echo "Activating virtual environment..."
source /home/site/wwwroot/venv/bin/activate

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install --no-cache-dir -r /home/site/wwwroot/requirements-minimal.txt

echo "Starting Gunicorn with Uvicorn workers..."
cd /home/site/wwwroot
gunicorn -c gunicorn.conf.py main:app

