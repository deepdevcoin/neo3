"""
Safe mouse control with rate limiting and validation
"""
import time
from typing import Dict, Any
from tools import Tool, ToolCategory, ToolBehavior

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ pyautogui not installed. Run: pip install pyautogui")


class MouseClick(Tool):
    name = "mouse_click"
    description = """Click at specific screen coordinates.

Use after detecting UI elements. Moves mouse smoothly then clicks.

Inputs:
- x (int, required): X coordinate
- y (int, required): Y coordinate  
- button (string, optional): "left" (default), "right", or "middle"
- clicks (int, optional): Number of clicks, default 1 (use 2 for double-click)

Returns: success, x, y, button, clicks

Workflow:
1. detect_ui_elements(template="button") → Get {x, y}
2. mouse_click(x=result.x, y=result.y) → Click it"""
    
    args = {
        "x": "int",
        "y": "int",
        "button": "string|null",
        "clicks": "int|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.3
    
    success_keys = ["success"]
    
    example_usage = """mouse_click(x=150, y=80)
→ Clicks left button at (150, 80)

mouse_click(x=500, y=300, clicks=2)
→ Double-clicks at (500, 300)"""
    
    def run(self, x: int, y: int, button: str = "left", clicks: int = 1) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        # Validate coordinates
        screen_width, screen_height = pyautogui.size()
        
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            return {
                "success": False,
                "error": f"coordinates out of bounds",
                "details": f"Screen size: {screen_width}x{screen_height}",
                "provided": f"({x}, {y})"
            }
        
        # Validate button
        valid_buttons = ["left", "right", "middle"]
        if button not in valid_buttons:
            return {
                "success": False,
                "error": f"invalid button '{button}'",
                "valid": valid_buttons
            }
        
        # Validate clicks
        if clicks < 1 or clicks > 3:
            return {
                "success": False,
                "error": "clicks must be 1-3"
            }
        
        try:
            # Pre-click delay
            time.sleep(0.2)
            
            # Move smoothly
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.1)
            
            # Click
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
            
            # Post-click delay
            time.sleep(0.2)
            
            return {
                "success": True,
                "x": x,
                "y": y,
                "button": button,
                "clicks": clicks
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "x": x,
                "y": y
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("success"):
            return f"Clicked at ({result['x']}, {result['y']})"
        return f"Click failed: {result.get('error', 'unknown')}"


class MouseMove(Tool):
    name = "mouse_move"
    description = """Move mouse cursor to coordinates without clicking.

Useful for hover actions or positioning.

Inputs:
- x (int): Target X coordinate
- y (int): Target Y coordinate
- smooth (bool): If true, moves smoothly over time

Returns: success, x, y, smooth"""
    
    args = {
        "x": "int",
        "y": "int",
        "smooth": "bool|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.2
    
    success_keys = ["success"]
    
    def run(self, x: int, y: int, smooth: bool = True) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        # Validate coordinates
        screen_width, screen_height = pyautogui.size()
        
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            return {
                "success": False,
                "error": "coordinates out of bounds"
            }
        
        try:
            duration = 0.3 if smooth else 0
            pyautogui.moveTo(x, y, duration=duration)
            time.sleep(0.1)
            
            return {
                "success": True,
                "x": x,
                "y": y,
                "smooth": smooth
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class MouseScroll(Tool):
    name = "mouse_scroll"
    description = """Scroll mouse wheel up or down.

Positive amount scrolls up, negative scrolls down.

Inputs:
- amount (int): Scroll amount (positive=up, negative=down)
- x (int, optional): Scroll at specific X position
- y (int, optional): Scroll at specific Y position

Returns: success, amount, direction, x, y"""
    
    args = {
        "amount": "int",
        "x": "int|null",
        "y": "int|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.2
    
    success_keys = ["success"]
    
    def run(self, amount: int, x: int = None, y: int = None) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        try:
            # Move to position if specified
            if x is not None and y is not None:
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
            
            # Scroll
            pyautogui.scroll(amount)
            time.sleep(0.1)
            
            direction = "up" if amount > 0 else "down"
            
            return {
                "success": True,
                "amount": abs(amount),
                "direction": direction,
                "x": x,
                "y": y
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class MouseDrag(Tool):
    name = "mouse_drag"
    description = """Drag from one position to another.

Useful for selecting text, moving windows, or drag-and-drop.

Inputs:
- x1, y1 (int): Start coordinates
- x2, y2 (int): End coordinates
- button (string, optional): "left", "right", "middle"
- duration (float, optional): Drag duration in seconds

Returns: success, x1, y1, x2, y2, button"""
    
    args = {
        "x1": "int",
        "y1": "int",
        "x2": "int",
        "y2": "int",
        "button": "string|null",
        "duration": "float|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.3
    
    success_keys = ["success"]
    
    def run(self, x1: int, y1: int, x2: int, y2: int, 
            button: str = "left", duration: float = 0.5) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        valid_buttons = ["left", "right", "middle"]
        if button not in valid_buttons:
            return {
                "success": False,
                "error": f"invalid button '{button}'"
            }
        
        try:
            # Move to start
            pyautogui.moveTo(x1, y1, duration=0.2)
            time.sleep(0.1)
            
            # Drag to end
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration, button=button)
            time.sleep(0.2)
            
            return {
                "success": True,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "button": button
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GetMousePosition(Tool):
    name = "get_mouse_position"
    description = """Get current mouse cursor position.

Useful for debugging or recording positions.

No inputs required.

Returns: success, x, y"""
    
    args = {}
    
    category = ToolCategory.DETECTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.0
    
    success_keys = ["success"]
    
    def run(self) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        try:
            x, y = pyautogui.position()
            
            return {
                "success": True,
                "x": x,
                "y": y
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }