from overlay.overlay_manager import manager
import threading
import time


def main_logic():
    """Your main program logic runs here"""
    time.sleep(0.5)  # Wait for Qt to initialize
    
    print("Adding shapes from background thread...")
    manager.add_circle(500, 500)
    manager.add_rect(300, 300, 900, 900)
    
    print("Overlay running... Press Ctrl+C to exit")
    while True:
        time.sleep(1)


# Initialize Qt in main thread
manager.initialize()

# Run your logic in a background thread
logic_thread = threading.Thread(target=main_logic, daemon=True)
logic_thread.start()

# Start Qt event loop in main thread (blocking)
manager.start()