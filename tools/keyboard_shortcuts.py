"""
Safe keyboard shortcuts with error handling
"""
import time
from typing import Dict, Any, Optional
from tools import Tool, ToolCategory, ToolBehavior

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ pyautogui not installed. Run: pip install pyautogui")


SHORTCUT_MAP = {
    # Applications
    "browser": ["alt", "b"],
    "terminal": ["alt", "t"],
    "finder": ["alt", "f"],
    "file manager": ["alt", "f"],
    "files": ["alt", "f"],
    
    # Browser
    "new tab": ["ctrl", "t"],
    "close tab": ["ctrl", "w"],
    "reopen tab": ["ctrl", "shift", "t"],
    "next tab": ["ctrl", "tab"],
    "previous tab": ["ctrl", "shift", "tab"],
    "refresh": ["ctrl", "r"],
    "hard refresh": ["ctrl", "shift", "r"],
    "address bar": ["ctrl", "l"],
    "bookmarks": ["ctrl", "shift", "b"],
    "history": ["ctrl", "h"],
    "downloads": ["ctrl", "j"],
    "find": ["ctrl", "f"],
    "fullscreen": ["f11"],
    "developer tools": ["f12"],
    
    # Terminal
    "new terminal tab": ["ctrl", "shift", "t"],
    "close terminal": ["ctrl", "shift", "w"],
    "clear terminal": ["ctrl", "l"],
    
    # Text editing
    "copy": ["ctrl", "c"],
    "paste": ["ctrl", "v"],
    "cut": ["ctrl", "x"],
    "undo": ["ctrl", "z"],
    "redo": ["ctrl", "shift", "z"],
    "select all": ["ctrl", "a"],
    "save": ["ctrl", "s"],
    
    # Window management
    "close window": ["alt", "f4"],
    "minimize": ["alt", "f9"],
    "maximize": ["alt", "f10"],
    "switch window": ["alt", "tab"],
}


ALIASES = {
    "open browser": "browser",
    "launch browser": "browser",
    "open terminal": "terminal",
    "open files": "file manager",
    "reload": "refresh",
    "go fullscreen": "fullscreen",
}


def fuzzy_match_shortcut(query: str) -> Optional[str]:
    """Find best matching shortcut"""
    query_lower = query.lower().strip()
    
    # Exact match
    if query_lower in SHORTCUT_MAP:
        return query_lower
    
    # Alias match
    if query_lower in ALIASES:
        return ALIASES[query_lower]
    
    # Substring match
    for key in SHORTCUT_MAP.keys():
        if query_lower in key or key in query_lower:
            return key
    
    # Word matching
    query_words = set(query_lower.split())
    best_match = None
    best_score = 0
    
    for key in SHORTCUT_MAP.keys():
        key_words = set(key.split())
        score = len(query_words & key_words)
        if score > best_score:
            best_score = score
            best_match = key
    
    return best_match if best_score > 0 else None


class KeyboardShortcut(Tool):
    name = "keyboard_shortcut"
    description = """Execute keyboard shortcuts for common actions.

Supports application launching, browser control, text editing, and window management.

Common actions:
- Applications: "browser", "terminal", "files"
- Browser: "new tab", "close tab", "refresh", "address bar"
- Text: "copy", "paste", "save", "undo"
- Windows: "close window", "switch window"

Uses fuzzy matching - similar phrases work (e.g., "open browser" = "browser").

Input: action (string) - Action name
Returns: success, action, keys, executed"""
    
    args = {"action": "string"}
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.8
    
    success_keys = ["success"]
    
    example_usage = """keyboard_shortcut(action="browser")
→ Executes Alt+B to open Brave

keyboard_shortcut(action="new tab")
→ Executes Ctrl+T for new browser tab"""
    
    def run(self, action: str) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "error": "pyautogui not installed"
            }
        
        matched_action = fuzzy_match_shortcut(action)
        
        if not matched_action:
            return {
                "success": False,
                "error": "unknown_action",
                "action": action,
                "hint": "Try: 'browser', 'new tab', 'terminal'"
            }
        
        keys = SHORTCUT_MAP[matched_action]
        
        try:
            # Safe execution with delay
            time.sleep(0.2)
            pyautogui.hotkey(*keys)
            time.sleep(0.3)
            
            return {
                "success": True,
                "action": matched_action,
                "keys": keys,
                "executed": " + ".join(keys)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": matched_action
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("success"):
            return f"Executed: {result.get('executed')}"
        return f"Failed: {result.get('error', 'unknown error')}"