import os
import uuid
import cv2
import pytesseract
from tools import Tool, ToolCategory, ToolBehavior
from vision.vision import capture_fullscreen

DEBUG_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "debug_outputs"
)
os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)


# =====================================================
# DETECT TEXT TOOL
# =====================================================

class DetectText(Tool):
    name = "detect_text"
    description = """Detect and read text on screen using OCR.

Scans entire screen and finds text. Optional filter by search term.

Input: text (string, optional) - If provided, only returns matches

Returns: found (bool), count (int), items (list), debug_image (path)

Each item contains: text, x, y, w, h

Use cases:
- Finding specific text to click near it
- Reading labels, buttons, UI text
- Verifying expected text is displayed

Workflow:
1. detect_text(text="Submit") → Find text
2. If found, use coordinates for mouse_click"""
    
    args = {"text": "string|null"}
    
    category = ToolCategory.DETECTION
    behavior = ToolBehavior.TERMINAL
    execution_delay = 0.0
    
    success_keys = ["found"]
    
    example_usage = """detect_text(text="Login")
→ Searches for "Login" text
→ Returns: {found: true, count: 1, items: [{text: "Login", x: 500, y: 300}]}"""
    
    def run(self, text: str = None) -> dict:
        try:
            screen = capture_fullscreen()
            
            if screen is None:
                return {
                    "error": "capture_failed",
                    "found": False,
                    "count": 0
                }
            
            # OCR
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            items = []
            for i in range(len(data["text"])):
                word = data["text"][i].strip()
                if not word:
                    continue
                
                # Filter by search term if provided
                if text and text.lower() not in word.lower():
                    continue
                
                items.append({
                    "text": word,
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "w": data["width"][i],
                    "h": data["height"][i]
                })
            
            # Save debug image
            dbg = screen.copy()
            for item in items:
                cv2.rectangle(
                    dbg,
                    (item["x"], item["y"]),
                    (item["x"] + item["w"], item["y"] + item["h"]),
                    (0, 255, 0), 2
                )
                cv2.putText(
                    dbg, item["text"],
                    (item["x"], item["y"] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 255, 0), 1
                )
            
            fname = f"text_detect_{uuid.uuid4().hex[:8]}.png"
            save_path = os.path.join(DEBUG_OUTPUT_DIR, fname)
            cv2.imwrite(save_path, dbg)
            
            result = {
                "found": len(items) > 0,
                "count": len(items),
                "items": items[:20],  # Limit to first 20
                "debug_image": save_path
            }
            
            if text:
                result["search_term"] = text
            
            return result
            
        except Exception as e:
            return {
                "found": False,
                "count": 0,
                "error": str(e)
            }
