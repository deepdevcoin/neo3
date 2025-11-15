from tools import Tool, ToolCategory, ToolBehavior
from overlay.overlay_manager import manager


class DrawOverlay(Tool):
    name = "draw_overlay"
    description = """Draw visual overlays on screen to highlight UI elements.

Draws shapes on transparent overlay:
- Circle: For point elements - use 2 coordinates
- Rectangle: For regions - use 4 coordinates

Input: coords (string) - Space-separated numbers:
  "x y" → Circle at (x, y)
  "x1 y1 x2 y2" → Rectangle from (x1,y1) to (x2,y2)
  "clear" → Remove all overlays

CRITICAL: 
- Use EXACT coordinates from detect tools
- Only use when user explicitly asks to "highlight", "show", or "mark"
- Do NOT use for simple tasks like "open browser" or "click button"

Returns: ok (bool), type ("circle", "rect", or "clear"), coords (list)"""
    
    args = {"coords": "string"}
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.TERMINAL
    execution_delay = 0.0
    
    success_keys = ["ok"]
    
    example_usage = """After detect_ui_elements returns {x: 150, y: 80}:
draw_overlay(coords="150 80") → Circle at element

After detect_ui_regions returns {x1: 50, y1: 35, x2: 1870, y2: 75}:
draw_overlay(coords="50 35 1870 75") → Rectangle around region"""
    
    def run(self, coords: str) -> dict:
        try:
            # Handle clear command
            if coords.lower().strip() == "clear":
                manager.clear()
                return {"ok": True, "type": "clear"}
            
            # Parse coordinates
            clean = coords.replace(",", " ").replace(";", " ").split()
            
            try:
                nums = [int(float(x)) for x in clean]
            except ValueError:
                return {
                    "error": "invalid coordinates - must be numbers",
                    "ok": False
                }
            
            # Circle (2 coords)
            if len(nums) == 2:
                x, y = nums
                manager.add_circle(x, y)
                return {"ok": True, "type": "circle", "coords": nums}
            
            # Rectangle (4 coords)
            elif len(nums) == 4:
                x1, y1, x2, y2 = nums
                manager.add_rect(x1, y1, x2, y2)
                return {"ok": True, "type": "rect", "coords": nums}
            
            else:
                return {
                    "error": "need 2 coords for circle or 4 for rectangle",
                    "ok": False
                }
        
        except Exception as e:
            return {
                "error": str(e),
                "ok": False
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("ok"):
            overlay_type = result.get("type", "unknown")
            if overlay_type == "clear":
                return "Overlay cleared"
            elif overlay_type == "circle":
                coords = result.get("coords", [])
                return f"Circle at ({coords[0]}, {coords[1]})"
            elif overlay_type == "rect":
                coords = result.get("coords", [])
                return f"Rectangle drawn"
        return f"Overlay failed: {result.get('error', 'unknown')}"