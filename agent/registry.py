"""
Production-grade tool registry with safety controls
"""
import pkgutil
import importlib
import time
from typing import Dict, Any
from tools import Tool


class ToolRegistry:
    """Safe tool registry with rate limiting and conflict detection"""
    
    def __init__(self):
        self.tools = {}
        self.last_call_time = {}
        self.call_count = {}
        self.last_tool = None
        
        # Conflict rules: tool -> list of conflicting tools
        self.conflicts = {
            "draw_overlay": ["keyboard_shortcut", "mouse_click", "type_text"],
            "keyboard_shortcut": ["draw_overlay"],
            "mouse_click": ["draw_overlay"],
        }
        
        # Minimum delay between calls to same tool
        self.min_tool_cooldown = 0.5
    
    def load_all(self):
        """Load all tool classes"""
        import tools
        
        loaded = 0
        for _, module_name, _ in pkgutil.iter_modules(tools.__path__):
            try:
                module = importlib.import_module(f"tools.{module_name}")
                
                for obj in module.__dict__.values():
                    if isinstance(obj, type) and issubclass(obj, Tool) and obj is not Tool:
                        instance = obj()
                        self.tools[instance.name] = instance
                        self.last_call_time[instance.name] = 0
                        self.call_count[instance.name] = 0
                        loaded += 1
            except Exception as e:
                print(f"⚠️ Failed to load module {module_name}: {e}")
        
        print(f"✅ Loaded {loaded} tools")
    
    def call(self, tool_name: str, args: Any) -> Dict[str, Any]:
        """Execute tool with safety checks"""
        tool = self.tools.get(tool_name)
        
        if not tool:
            return {
                "error": f"unknown_tool",
                "tool": tool_name,
                "success": False
            }
        
        # Fix null arguments
        if args is None:
            args = {}
        
        if not isinstance(args, dict):
            return {
                "error": "invalid_arguments",
                "details": f"expected dict, got {type(args).__name__}",
                "received": args,
                "success": False
            }
        
        # Check conflicts with last tool
        if self._has_conflict(tool_name):
            return {
                "error": "tool_conflict",
                "details": f"{tool_name} conflicts with recent {self.last_tool}",
                "suggestion": "Wait before calling this tool",
                "success": False
            }
        
        # Rate limiting per tool
        now = time.time()
        last_call = self.last_call_time.get(tool_name, 0)
        
        if now - last_call < self.min_tool_cooldown:
            wait_time = self.min_tool_cooldown - (now - last_call)
            time.sleep(wait_time)
        
        # Execute tool
        try:
            result = tool.run(**args)
            
            # Update tracking
            self.last_call_time[tool_name] = time.time()
            self.call_count[tool_name] += 1
            self.last_tool = tool_name
            
            return result
            
        except TypeError as e:
            return {
                "error": "bad_tool_arguments",
                "tool": tool_name,
                "details": str(e),
                "success": False
            }
        except Exception as e:
            return {
                "error": "tool_runtime_exception",
                "tool": tool_name,
                "details": str(e),
                "success": False
            }
    
    def _has_conflict(self, tool_name: str) -> bool:
        """Check if tool conflicts with recently called tool"""
        if not self.last_tool:
            return False
        
        conflicts = self.conflicts.get(tool_name, [])
        
        if self.last_tool in conflicts:
            # Check if enough time has passed
            now = time.time()
            last_call = self.last_call_time.get(self.last_tool, 0)
            
            if now - last_call < 2.0:  # 2 second conflict window
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_calls = sum(self.call_count.values())
        
        top_tools = sorted(
            self.call_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_calls": total_calls,
            "unique_tools": len([c for c in self.call_count.values() if c > 0]),
            "top_tools": top_tools
        }