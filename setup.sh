#!/bin/bash

# Exit on error
set -e

echo "Starting setup..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found. Please install Python 3."
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "Virtual environment 'venv' already exists."
fi

# Activate virtual environment
source venv/bin/activate
echo "Virtual environment activated."

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Setup .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "Example .env created. PLEASE EDIT .env WITH YOUR CREDENTIALS!"
    else
        echo "Warning: .env.example not found. Skipping .env creation."
    fi
else
    echo ".env file already exists."
fi

echo ""
echo "Setup complete!"
echo "To run the script:"
echo "1. Edit .env with your Jira details (if you haven't already)"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python3 fetch_jira_data.py"
