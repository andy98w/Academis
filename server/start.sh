#!/bin/bash

VENV_PYTHON="/Users/andywu/Academis/server/venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV_PYTHON"
    echo "Please run: /opt/homebrew/bin/python3.11 -m venv venv"
    echo "Then: venv/bin/pip install -r requirements.txt"
    exit 1
fi

echo "Starting server with virtual environment Python..."
$VENV_PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload