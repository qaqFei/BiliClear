#!/bin/bash

cd ..

# Create a virtual environment
python3 -m venv release-ven

# Activate the virtual environment
source release-ven/bin/activate

# Install required packages
pip install -r requirements.txt
pip install pyinstaller

# Build executables with PyInstaller
pyinstaller biliclear.py -i ./res/icon.ico
pyinstaller biliclear_gui_webui.py -i ./res/icon.ico
pyinstaller biliclear_gui_qt.py -i ./res/icon.ico

# Copy built files to the current directory
cp -r dist/biliclear/* ./
cp -r dist/biliclear_gui_webui/* ./
cp -r dist/biliclear_gui_qt/* ./

# Clean up
rm -rf release-ven
rm -rf build
rm -rf dist
rm -f biliclear.spec
rm -f biliclear_gui_webui.spec
rm -f biliclear_gui_qt.spec
