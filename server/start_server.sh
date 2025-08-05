#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the server directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please create it first:"
    echo "python -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if run.py exists
if [ ! -f "run.py" ]; then
    echo "Error: run.py not found in server directory"
    exit 1
fi

# Start the server
echo "Starting Academis server..."
python run.py