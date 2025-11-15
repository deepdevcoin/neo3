"""
Safe vision detection tools with error handling
"""
import os
import uuid
import cv2
from typing import Dict, Any

from tools import Tool, ToolCategory, ToolBehavior
from vision.vision import capture_fullscreen, detect_all_templates
from vision.regions import REGION_MAP

DEBUG_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "debug_outputs"
)
os.makedirs(DEBUG_OUTPUT_DIR, exist_ok=True)


class DetectUIElements(Tool):
    name = "detect_ui_elements"
    description = """Detect specific UI elements (icons, buttons, logos) on screen.

Uses template matching to find visual elements and returns center coordinates.

Input: template (string) - EXACT template name from retrieve_ui_reference

Returns: found (bool), x (int), y (int), score (float), debug_image (path)

CRITICAL: Always use retrieve_ui_reference first to get correct template name.

Workflow:
1. retrieve_ui_reference(query="youtube logo") → Get best_key
2. detect_ui_elements(template=best_key) → Get coordinates
3. If found=true, use x,y for mouse_click or draw_overlay"""
    
    args = {"template": "string"}
    
    category = ToolCategory.DETECTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.0
    
    followup_suggestions = ["draw_overlay", "mouse_click"]
    success_keys = ["found"]
    
    example_usage = """detect_ui_elements(template="youtube_logo")
→ Returns: {found: true, x: 150, y: 80, score: 0.95}
→ Next: mouse_click(x=150, y=80)"""
    
    def run(self, template: str) -> dict:
        try:
            screen = capture_fullscreen()
            
            if screen is None:
                return {
                    "found": False,
                    "error": "screenshot_failed"
                }
            
            hits = detect_all_templates(screen)
            
            if template not in hits:
                return {
                    "found": False,
                    "template": template,
                    "hint": "Use retrieve_ui_reference to find correct template name"
                }
            
            hit = hits[template]
            x, y, score = hit["x"], hit["y"], hit["score"]
            
            # Save debug image
            fname = f"detect_{template}_{uuid.uuid4().hex[:8]}.png"
            save_path = os.path.join(DEBUG_OUTPUT_DIR, fname)
            
            dbg = screen.copy()
            cv2.circle(dbg, (x, y), 20, (0, 255, 0), 3)
            cv2.putText(dbg, template, (x-50, y-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imwrite(save_path, dbg)
            
            return {
                "found": True,
                "x": x,
                "y": y,
                "score": score,
                "template": template,
                "debug_image": save_path
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": str(e),
                "template": template
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("found"):
            return f"Found {result['template']} at ({result['x']}, {result['y']})"
        return f"Not found: {result.get('template', 'unknown')}"


class DetectUIRegions(Tool):
    name = "detect_ui_regions"
    description = """Get coordinates of predefined UI regions.

Returns bounding box for larger UI areas like sidebars, address bars, toolbars.

Input: region (string) - EXACT region name from retrieve_ui_reference

Returns: found (bool), x1, y1, x2, y2 (int), debug_image (path)

Coordinates define rectangle: (x1,y1) = top-left, (x2,y2) = bottom-right

CRITICAL: Always use retrieve_ui_reference first to get correct region name.

Workflow:
1. retrieve_ui_reference(query="address bar") → Get best_key
2. detect_ui_regions(region=best_key) → Get coordinates
3. Use x1,y1,x2,y2 for draw_overlay or calculate center for clicking"""
    
    args = {"region": "string"}
    
    category = ToolCategory.DETECTION
    behavior = ToolBehavior.INTERMEDIATE
    execution_delay = 0.0
    
    followup_suggestions = ["draw_overlay", "mouse_click"]
    success_keys = ["found"]
    
    example_usage = """detect_ui_regions(region="brave_address_bar")
→ Returns: {found: true, x1: 50, y1: 35, x2: 1870, y2: 75}
→ Next: draw_overlay(coords="50 35 1870 75")"""
    
    def run(self, region: str) -> dict:
        try:
            if region not in REGION_MAP:
                return {
                    "found": False,
                    "error": "unknown_region",
                    "region": region,
                    "hint": "Use retrieve_ui_reference to find correct region name"
                }
            
            x1, y1, x2, y2 = REGION_MAP[region]
            
            # Save debug image
            screen = capture_fullscreen()
            
            if screen is not None:
                fname = f"region_{region}_{uuid.uuid4().hex[:8]}.png"
                save_path = os.path.join(DEBUG_OUTPUT_DIR, fname)
                
                dbg = screen.copy()
                cv2.rectangle(dbg, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(dbg, region, (x1+10, y1+30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imwrite(save_path, dbg)
            else:
                save_path = None
            
            return {
                "found": True,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "region": region,
                "debug_image": save_path
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": str(e),
                "region": region
            }
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("found"):
            return f"Found region {result['region']}"
        return f"Region not found: {result.get('region', 'unknown')}"


class RetrieveUIReference(Tool):
    name = "retrieve_ui_reference"
    description = """Search for UI elements using natural language.

Performs semantic search across templates and regions to find exact technical names.

Input: query (string) - Natural language description of element

Returns: found (bool), best_key (exact name), type ("template" or "region"), 
         score (confidence), alternatives (other matches)

Query examples:
- "youtube logo" → best_key="youtube_logo", type="template"
- "browser address bar" → best_key="brave_address_bar", type="region"
- "close button" → best_key="close_button", type="template"

CRITICAL: Use the EXACT best_key in subsequent detect calls.

Workflow:
1. retrieve_ui_reference(query="address bar")
2. If type=="template": detect_ui_elements(template=best_key)
3. If type=="region": detect_ui_regions(region=best_key)"""
    
    args = {"query": "string"}
    
    category = ToolCategory.SEARCH
    behavior = ToolBehavior.REQUIRES_FOLLOWUP
    execution_delay = 0.0
    
    followup_suggestions = ["detect_ui_elements", "detect_ui_regions"]
    success_keys = ["found"]
    
    example_usage = """retrieve_ui_reference(query="youtube logo")
→ Returns: {found: true, best_key: "youtube_logo", type: "template"}
→ Next: detect_ui_elements(template="youtube_logo")"""
    
    def run(self, query: str) -> dict:
        try:
            from vision.vision import TEMPLATES
            
            query_lower = query.lower().strip()
            
            # Search templates
            template_matches = self._search_templates(query_lower, TEMPLATES)
            
            # Search regions
            region_matches = self._search_regions(query_lower)
            
            # Combine and rank
            all_matches = template_matches + region_matches
            
            if not all_matches:
                return {
                    "found": False,
                    "query": query,
                    "error": "no_matches",
                    "hint": "Try: 'youtube logo', 'address bar', 'sidebar', 'close button'"
                }
            
            # Sort by score
            all_matches.sort(key=lambda x: x["score"], reverse=True)
            
            best = all_matches[0]
            
            return {
                "found": True,
                "query": query,
                "best_key": best["key"],
                "type": best["type"],
                "score": round(best["score"], 3),
                "alternatives": [m["key"] for m in all_matches[1:4]]
            }
            
        except Exception as e:
            return {
                "found": False,
                "query": query,
                "error": str(e)
            }
    
    def _search_templates(self, query: str, templates: dict) -> list:
        """Search through templates"""
        matches = []
        
        for template_name in templates.keys():
            score = self._calculate_similarity(query, template_name)
            if score > 0.2:
                matches.append({
                    "key": template_name,
                    "type": "template",
                    "score": score
                })
        
        return matches
    
    def _search_regions(self, query: str) -> list:
        """Search through regions"""
        matches = []
        
        for region_name in REGION_MAP.keys():
            score = self._calculate_similarity(query, region_name)
            if score > 0.2:
                matches.append({
                    "key": region_name,
                    "type": "region",
                    "score": score
                })
        
        return matches
    
    def _calculate_similarity(self, query: str, target: str) -> float:
        """Calculate similarity score"""
        query = query.lower()
        target = target.lower()
        
        # Exact match
        if query == target:
            return 1.0
        
        # Substring match
        if query in target:
            return 0.9
        
        if target in query:
            return 0.85
        
        # Word matching
        query_words = set(query.replace("_", " ").replace("-", " ").split())
        target_words = set(target.replace("_", " ").replace("-", " ").split())
        
        # Remove stop words
        stop_words = {"the", "a", "an", "on", "in", "at", "to", "for", "of", "with"}
        query_words -= stop_words
        target_words -= stop_words
        
        if not query_words or not target_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_words & target_words)
        union = len(query_words | target_words)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # Boost if all query words present
        if query_words.issubset(target_words):
            jaccard *= 1.2
        
        return min(jaccard, 1.0)
    
    def get_result_summary(self, result: dict) -> str:
        if result.get("found"):
            key = result['best_key']
            ref_type = result['type']
            
            if ref_type == "template":
                return f"Found template '{key}' - use detect_ui_elements"
            else:
                return f"Found region '{key}' - use detect_ui_regions"
        
        return f"No match for '{result.get('query')}'"