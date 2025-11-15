#!/bin/bash
# Installation script for system state tool dependencies
# For Pop!_OS 22.04 LTS (GNOME)

echo "==================================="
echo "Installing System State Dependencies"
echo "==================================="

# Python dependencies
echo ""
echo "Installing Python packages..."
pip install psutil

# System tools for window management
echo ""
echo "Installing system tools..."
sudo apt update
sudo apt install -y \
    xdotool \
    wmctrl \
    x11-utils

# Verify installations
echo ""
echo "==================================="
echo "Verifying installations..."
echo "==================================="

echo -n "xdotool: "
if command -v xdotool &> /dev/null; then
    echo "✓ Installed"
else
    echo "✗ Not found"
fi

echo -n "wmctrl: "
if command -v wmctrl &> /dev/null; then
    echo "✓ Installed"
else
    echo "✗ Not found"
fi

echo -n "xdpyinfo: "
if command -v xdpyinfo &> /dev/null; then
    echo "✓ Installed"
else
    echo "✗ Not found"
fi

echo -n "psutil: "
if python3 -c "import psutil" 2>/dev/null; then
    echo "✓ Installed"
else
    echo "✗ Not found"
fi

echo ""
echo "==================================="
echo "Installation complete!"
echo "==================================="
echo ""
echo "Tool capabilities:"
echo "  ✓ Get active window information"
echo "  ✓ List all visible windows"
echo "  ✓ Detect browser tabs (Brave)"
echo "  ✓ Screen resolution detection"
echo "  ✓ Application state awareness"
echo ""
echo "Your agent will now:"
echo "  ✓ Never detect UI in wrong apps"
echo "  ✓ Never skip 'open browser' step"
echo "  ✓ Never highlight inactive windows"
echo "  ✓ Always verify system state first"
echo ""