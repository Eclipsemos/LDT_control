#!/bin/bash
# Startup script for MAVLink Gateway (Linux/Mac)

echo "============================================"
echo "  LDT MAVLink Gateway - Starting..."
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import pymavlink" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "Starting MAVLink Gateway..."
echo "Press Ctrl+C to stop"
echo ""

# Run the gateway
python3 mavlink_gateway.py

