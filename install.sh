#!/bin/bash

# Ollama Pro - Easy Installer for Linux
# This script handles system dependencies, virtual environment, and desktop integration.

echo "🚀 Starting Ollama Pro Installation..."

# 1. Install System Dependencies
echo "📦 Installing system dependencies (requires sudo)..."
sudo apt update
sudo apt install -y portaudio19-dev python3-pip python3-venv libasound2-dev

# 2. Create Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Libraries
echo "📥 Installing required Python libraries..."
./venv/bin/pip install -r requirements.txt

# 4. Create Desktop Launcher
echo "🖥️ Creating Desktop Launcher..."
DESKTOP_FILE="$HOME/.local/share/applications/ollama-pro.desktop"
ICON_PATH="/usr/share/icons/Yaru/scalable/devices/computer-chip-symbolic.svg"

# Use the current directory for the execution path
PROJECT_DIR=$(pwd)

cat <<EOF > $DESKTOP_FILE
[Desktop Entry]
Version=1.0
Type=Application
Name=Ollama Pro
Comment=Professional AI Engineering Workspace
Exec=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Icon=computer-chip-symbolic
Terminal=false
Categories=Development;Utility;
Keywords=AI;LLM;Ollama;
EOF

chmod +x $DESKTOP_FILE

# 5. Create a Copy on the Desktop
cp $DESKTOP_FILE ~/Desktop/
chmod +x ~/Desktop/ollama-pro.desktop

echo "✅ Installation Complete!"
echo "✨ You can now find Ollama Pro in your Application Menu or on your Desktop."
echo "🚀 To run manually: ./venv/bin/python main.py"
