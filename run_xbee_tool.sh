#!/bin/bash
echo "Starting XBee Configurator..."
python3 xbee_configurator.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to start. Please check if Python and dependencies are installed."
    echo "Run: pip3 install -r requirements.txt"
fi
