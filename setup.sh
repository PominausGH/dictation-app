#!/bin/bash
set -e

echo "=== Dictation App Setup ==="

# Install system dependencies
echo "[1/4] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y ydotool portaudio19-dev python3-venv python3-pip

# Enable and start ydotoold service (needed for Wayland)
echo "[2/4] Setting up ydotool daemon..."
sudo systemctl enable ydotoold
sudo systemctl start ydotoold

# Add user to input group (needed for ydotool without sudo)
echo "[3/4] Adding user to input group..."
sudo usermod -aG input "$USER"

# Create Python virtual environment
echo "[4/4] Creating Python virtual environment..."
cd "$(dirname "$0")"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== Setup Complete ==="
echo ""
echo "IMPORTANT: Log out and back in for group changes to take effect."
echo ""
echo "To run the dictation app:"
echo "  cd ~/dictation-app"
echo "  source venv/bin/activate"
echo "  python dictation.py"
echo ""
echo "Press Ctrl+Shift+D to toggle dictation on/off"
