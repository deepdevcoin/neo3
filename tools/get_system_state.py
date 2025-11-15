"""
Safe system state detection with error handling
"""
import subprocess
import re
from typing import Dict, Any, List, Optional
from tools import Tool, ToolCategory, ToolBehavior

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not installed (optional)")


class GetSystemState(Tool):
    name = "get_system_state"
    description = """Get comprehensive system state information.

Returns:
- Active application name and window title
- Active window ID and geometry (position, size)
- Browser info (if Brave is active): tab title
- List of visible windows with titles
- Screen resolution
- Likely visible UI regions

USE THIS FIRST before any UI interaction to ensure correct context.

No inputs required.

Returns: success, active_app, active_window_title, active_window_id, 
         active_window_geometry, browser_info, visible_windows, 
         screen_resolution, likely_visible_regions"""
    
    args = {}
    
    category = ToolCategory.DETECTION
    behavior = ToolBehavior.REQUIRES_FOLLOWUP
    execution_delay = 0.0
    
    followup_suggestions = ["keyboard_shortcut", "retrieve_ui_reference", "detect_ui_elements"]
    success_keys = ["success"]
    
    example_usage = """get_system_state()
→ Returns current state
→ If active_app != "brave", call keyboard_shortcut(action="browser")"""
    
    def run(self) -> dict:
        """Get comprehensive system state"""
        result = {
            "success": True,
            "active_app": None,
            "active_window_title": None,
            "active_window_id": None,
            "active_window_geometry": None,
            "browser_info": None,
            "visible_windows": [],
            "desktop_environment": "GNOME",
            "screen_resolution": self._get_screen_resolution(),
        }
        
        try:
            # Get active window
            active_window = self._get_active_window()
            if active_window:
                result.update(active_window)
            
            # Get visible windows
            result["visible_windows"] = self._get_visible_windows()
            
            # Browser info if active
            if result["active_app"] and "brave" in result["active_app"].lower():
                result["browser_info"] = self._get_brave_browser_info()
            
            # Detect visible UI regions
            result["likely_visible_regions"] = self._detect_visible_regions(result["active_app"])
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get active window information"""
        try:
            # Get window ID
            window_id = subprocess.check_output(
                ["xdotool", "getactivewindow"],
                stderr=subprocess.DEVNULL,
                timeout=2
            ).decode().strip()
            
            if not window_id:
                return None
            
            # Get window properties
            xprop_output = subprocess.check_output(
                ["xprop", "-id", window_id],
                stderr=subprocess.DEVNULL,
                timeout=2
            ).decode()
            
            # Parse title
            title_match = re.search(r'WM_NAME\(.*?\) = "(.*?)"', xprop_output)
            window_title = title_match.group(1) if title_match else "Unknown"
            
            # Parse class (app name)
            class_match = re.search(r'WM_CLASS\(.*?\) = "(.*?)", "(.*?)"', xprop_output)
            app_name = class_match.group(2) if class_match else "Unknown"
            
            # Get geometry
            geometry = subprocess.check_output(
                ["xdotool", "getwindowgeometry", window_id],
                stderr=subprocess.DEVNULL,
                timeout=2
            ).decode()
            
            pos_match = re.search(r'Position: (\d+),(\d+)', geometry)
            size_match = re.search(r'Geometry: (\d+)x(\d+)', geometry)
            
            geometry_dict = None
            if pos_match and size_match:
                geometry_dict = {
                    "x": int(pos_match.group(1)),
                    "y": int(pos_match.group(2)),
                    "width": int(size_match.group(1)),
                    "height": int(size_match.group(2))
                }
            
            # Get process info if psutil available
            if PSUTIL_AVAILABLE:
                try:
                    pid_match = re.search(r'_NET_WM_PID\(CARDINAL\) = (\d+)', xprop_output)
                    if pid_match:
                        pid = int(pid_match.group(1))
                        process = psutil.Process(pid)
                        app_name = process.name()
                except:
                    pass
            
            return {
                "active_window_id": window_id,
                "active_window_title": window_title,
                "active_app": app_name,
                "active_window_geometry": geometry_dict
            }
            
        except subprocess.TimeoutExpired:
            return None
        except subprocess.CalledProcessError:
            return None
        except Exception:
            return None
    
    def _get_visible_windows(self) -> List[Dict[str, Any]]:
        """Get list of visible windows"""
        try:
            # Try wmctrl first
            output = subprocess.check_output(
                ["wmctrl", "-l"],
                stderr=subprocess.DEVNULL,
                timeout=2
            ).decode()
            
            windows = []
            for line in output.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id = parts[0]
                    desktop = parts[1]
                    title = parts[3]
                    
                    # Get app name
                    try:
                        xprop_out = subprocess.check_output(
                            ["xprop", "-id", window_id, "WM_CLASS"],
                            stderr=subprocess.DEVNULL,
                            timeout=1
                        ).decode()
                        
                        class_match = re.search(r'"(.*?)", "(.*?)"', xprop_out)
                        app = class_match.group(2) if class_match else "Unknown"
                    except:
                        app = "Unknown"
                    
                    windows.append({
                        "window_id": window_id,
                        "title": title,
                        "app": app,
                        "desktop": desktop
                    })
                
                # Limit to prevent hanging
                if len(windows) >= 20:
                    break
            
            return windows
            
        except subprocess.TimeoutExpired:
            return []
        except subprocess.CalledProcessError:
            # Fallback to xdotool
            try:
                output = subprocess.check_output(
                    ["xdotool", "search", "--onlyvisible", "--name", ""],
                    stderr=subprocess.DEVNULL,
                    timeout=2
                ).decode()
                
                windows = []
                for window_id in output.strip().split('\n')[:20]:
                    if window_id:
                        try:
                            title = subprocess.check_output(
                                ["xdotool", "getwindowname", window_id],
                                stderr=subprocess.DEVNULL,
                                timeout=1
                            ).decode().strip()
                            
                            windows.append({
                                "window_id": window_id,
                                "title": title,
                                "app": "Unknown"
                            })
                        except:
                            continue
                
                return windows
            except:
                return []
        except Exception:
            return []
    
    def _get_brave_browser_info(self) -> Optional[Dict[str, Any]]:
        """Get Brave browser tab information"""
        try:
            active_window = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"],
                stderr=subprocess.DEVNULL,
                timeout=1
            ).decode().strip()
            
            if " - Brave" in active_window:
                tab_title = active_window.replace(" - Brave", "").strip()
                
                return {
                    "browser": "Brave",
                    "active_tab_title": tab_title,
                    "window_title": active_window
                }
            
            return None
            
        except:
            return None
    
    def _get_screen_resolution(self) -> str:
        """Get screen resolution"""
        try:
            output = subprocess.check_output(
                ["xdpyinfo"],
                stderr=subprocess.DEVNULL,
                timeout=1
            ).decode()
            
            match = re.search(r'dimensions:\s+(\d+x\d+)', output)
            if match:
                return match.group(1)
            
            return "1920x1080"  # Default
            
        except:
            return "1920x1080"
    
    def _detect_visible_regions(self, active_app: Optional[str]) -> List[str]:
        """Determine visible UI regions based on active app"""
        if not active_app:
            return []
        
        app_lower = active_app.lower()
        visible = []
        
        # Browser
        if any(browser in app_lower for browser in ["brave", "chrome", "firefox", "chromium"]):
            visible.extend([
                "browser_address_bar",
                "browser_tabs",
                "browser_toolbar",
                "browser_sidebar",
                "browser_content_area"
            ])
        
        # Terminal
        elif "terminal" in app_lower or "gnome-terminal" in app_lower:
            visible.extend([
                "terminal_content",
                "terminal_tabs"
            ])
        
        # File manager
        elif "nautilus" in app_lower or "files" in app_lower:
            visible.extend([
                "file_manager_sidebar",
                "file_manager_content",
                "file_manager_toolbar"
            ])
        
        # Code editors
        elif any(editor in app_lower for editor in ["code", "vscode", "sublime", "atom"]):
            visible.extend([
                "editor_sidebar",
                "editor_content",
                "editor_tabs"
            ])
        
        return visible
    
    def get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate readable summary"""
        if not result.get("success"):
            return "Failed to get system state"
        
        active_app = result.get("active_app", "Unknown")
        active_title = result.get("active_window_title", "Unknown")
        window_count = len(result.get("visible_windows", []))
        
        summary = f"Active: {active_app} - '{active_title}' ({window_count} windows visible)"
        
        if result.get("browser_info"):
            browser_info = result["browser_info"]
            tab_title = browser_info.get("active_tab_title", "Unknown tab")
            summary += f" | Tab: '{tab_title}'"
        
        return summary