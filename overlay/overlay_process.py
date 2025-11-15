#!/usr/bin/env python3
"""
Separate process for running the Qt overlay.
This avoids threading issues with PyQt5.
"""

import sys
import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from overlay.overlay_window import OverlayWindow


class OverlayProcess:
    def __init__(self, command_file):
        self.command_file = command_file
        self.trigger_file = command_file + '.trigger'
        self.app = QApplication(sys.argv)
        self.overlay = OverlayWindow()
        
        # Set up timer to check for commands
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_commands)
        self.timer.start(100)  # Check every 100ms
        
        print("Overlay process ready")
    
    def check_commands(self):
        """Check for new commands from the trigger file"""
        if not os.path.exists(self.trigger_file):
            return
        
        try:
            # Read command
            with open(self.command_file, 'r') as f:
                cmd_data = json.load(f)
            
            # Remove trigger
            os.unlink(self.trigger_file)
            
            # Execute command
            command = cmd_data.get('command')
            data = cmd_data.get('data', {})
            
            if command == 'add_circle':
                self.overlay.add_circle(data['x'], data['y'])
            elif command == 'add_rect':
                self.overlay.add_rect(
                    data['x1'], data['y1'], 
                    data['x2'], data['y2']
                )
            elif command == 'clear':
                self.overlay.clear_shapes()
            elif command == 'close':
                self.app.quit()
        
        except Exception as e:
            print(f"Error processing command: {e}")
    
    def run(self):
        """Start the Qt event loop"""
        return self.app.exec_()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: overlay_process.py <command_file>")
        sys.exit(1)
    
    command_file = sys.argv[1]
    process = OverlayProcess(command_file)
    sys.exit(process.run())