"""
Safe keyboard typing with validation and delays
"""
import time
from typing import Dict, Any
from tools import Tool, ToolCategory, ToolBehavior

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ pyautogui not installed")


class TypeText(Tool):
    name = "type_text"
    description = """Type text at current cursor position.

Use after clicking on text field or focusing input area.

Inputs:
- text (string, required): Text to type
- interval (float, optional): Delay between keypresses (default 0.05)

Returns: success, text (truncated), char_count, interval

Workflow:
1. Click on input field first
2. Call type_text with your text"""
    
    args = {
        "text": "string",
        "interval": "float|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.2
    
    success_keys = ["success"]
    
    example_usage = """type_text(text="Hello World", interval=0.05)
→ Types text with 0.05s delay between keys"""
    
    def run(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        if not text:
            return {
                "success": False,
                "error": "text cannot be empty"
            }
        
        # Validate interval
        if interval < 0 or interval > 1:
            return {
                "success": False,
                "error": "interval must be 0-1 seconds"
            }
        
        try:
            # Pre-type delay
            time.sleep(0.2)
            
            # Type text
            pyautogui.write(text, interval=interval)
            
            # Post-type delay
            time.sleep(0.1)
            
            return {
                "success": True,
                "text": text[:50] + "..." if len(text) > 50 else text,
                "char_count": len(text),
                "interval": interval
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("success"):
            return f"Typed {result['char_count']} characters"
        return f"Type failed: {result.get('error')}"


class PressKey(Tool):
    name = "press_key"
    description = """Press a specific key or special key.

For special keys like Enter, Tab, Arrow keys, etc.

Inputs:
- key (string, required): Key name (e.g., "enter", "tab", "up", "f5")
- presses (int, optional): Number of times to press (default 1)

Returns: success, key, presses

Common keys: enter, tab, escape, space, backspace, delete,
up, down, left, right, home, end, f1-f12"""
    
    args = {
        "key": "string",
        "presses": "int|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.2
    
    success_keys = ["success"]
    
    example_usage = """press_key(key="enter")
→ Presses Enter key once

press_key(key="tab", presses=3)
→ Presses Tab key 3 times"""
    
    def run(self, key: str, presses: int = 1) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        valid_keys = [
            "enter", "return", "tab", "space", "backspace", "delete",
            "up", "down", "left", "right",
            "home", "end", "pageup", "pagedown",
            "shift", "ctrl", "alt", "win", "command",
            "f1", "f2", "f3", "f4", "f5", "f6",
            "f7", "f8", "f9", "f10", "f11", "f12",
            "escape", "esc", "insert", "pause", "printscreen",
            "capslock", "numlock", "scrolllock"
        ]
        
        key_lower = key.lower()
        
        # Allow single characters or valid special keys
        if len(key) > 1 and key_lower not in valid_keys:
            return {
                "success": False,
                "error": f"invalid key '{key}'",
                "hint": "Use single characters or special keys like 'enter', 'tab', etc."
            }
        
        if presses < 1 or presses > 10:
            return {
                "success": False,
                "error": "presses must be 1-10"
            }
        
        try:
            time.sleep(0.2)
            
            for _ in range(presses):
                pyautogui.press(key)
                time.sleep(0.05)
            
            time.sleep(0.1)
            
            return {
                "success": True,
                "key": key,
                "presses": presses
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "key": key
            }


class HoldKeys(Tool):
    name = "hold_keys"
    description = """Hold down multiple keys simultaneously.

For key combinations like Ctrl+C, Alt+Tab, etc.
Note: Use keyboard_shortcut tool for common combinations.

Inputs:
- keys (string, required): Comma-separated keys (e.g., "ctrl,c")

Returns: success, keys

Example: "ctrl,shift,t" for Ctrl+Shift+T"""
    
    args = {
        "keys": "string"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.2
    
    success_keys = ["success"]
    
    def run(self, keys: str) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        key_list = [k.strip().lower() for k in keys.split(",")]
        
        if not key_list:
            return {
                "success": False,
                "error": "keys cannot be empty"
            }
        
        if len(key_list) > 4:
            return {
                "success": False,
                "error": "maximum 4 keys in combination"
            }
        
        try:
            time.sleep(0.2)
            pyautogui.hotkey(*key_list)
            time.sleep(0.1)
            
            return {
                "success": True,
                "keys": " + ".join(key_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "keys": keys
            }


class ClearAndType(Tool):
    name = "clear_and_type"
    description = """Clear existing text in field and type new text.

Performs Ctrl+A (select all) then types replacement text.

Inputs:
- text (string, required): Text to type
- interval (float, optional): Delay between keypresses (default 0.05)

Returns: success, text (truncated), char_count

Workflow:
1. detect_ui_regions(region="input_field")
2. mouse_click(x=center_x, y=center_y)
3. clear_and_type(text="new text")"""
    
    args = {
        "text": "string",
        "interval": "float|null"
    }
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.2
    
    success_keys = ["success"]
    
    example_usage = """clear_and_type(text="https://example.com")
→ Selects all and types URL"""
    
    def run(self, text: str, interval: float = 0.05) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        if not text:
            return {
                "success": False,
                "error": "text cannot be empty"
            }
        
        if interval < 0 or interval > 1:
            return {
                "success": False,
                "error": "interval must be 0-1 seconds"
            }
        
        try:
            # Select all
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Type new text
            pyautogui.write(text, interval=interval)
            time.sleep(0.1)
            
            return {
                "success": True,
                "text": text[:50] + "..." if len(text) > 50 else text,
                "char_count": len(text)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("success"):
            return f"Cleared and typed {result['char_count']} characters"
        return f"Clear and type failed: {result.get('error')}"