"""
UI Reference Retrieval Tool - RAG-based semantic search for UI elements
Searches through templates and regions using natural language queries
"""
import os
from tools import Tool, ToolCategory, ToolBehavior
from vision.vision import TEMPLATES
from vision.regions import REGION_MAP


class RetrieveUIReference(Tool):
    name = "retrieve_ui_reference"
    description = """Search for UI elements using natural language queries and get the exact technical reference name.

This tool performs semantic search across available UI templates (specific elements like buttons, icons, logos) and regions (larger areas like sidebars, address bars, toolbars).

Query examples:
- "youtube logo" → Returns: best_key="youtube_logo", type="template"
- "browser address bar" → Returns: best_key="brave_address_bar", type="region"
- "close button" → Returns: best_key="close_button", type="template"
- "sidebar" → Returns: best_key="browser_sidebar", type="region"

CRITICAL: Use the EXACT "best_key" value returned by this tool in subsequent detect_ui_elements or detect_ui_regions calls.

Returns: found (bool), best_key (exact name to use), type ("template" or "region"), score (confidence), alternatives (other possible matches)"""
    
    args = {"query": "string"}
    
    category = ToolCategory.SEARCH
    behavior = ToolBehavior.REQUIRES_FOLLOWUP
    execution_delay = 0.0
    
    followup_suggestions = ["detect_ui_elements", "detect_ui_regions"]
    success_keys = ["found"]
    
    example_usage = """Step 1: retrieve_ui_reference(query="address bar")
Step 2: Use result.best_key in next tool
If result.type == "template": detect_ui_elements(template=result.best_key)
If result.type == "region": detect_ui_regions(region=result.best_key)"""
    
    def run(self, query: str) -> dict:
        """
        Search for UI reference using natural language query.
        Returns the best matching template or region name.
        """
        query_lower = query.lower().strip()
        
        # Search in templates (specific UI elements like logos, buttons)
        template_matches = self._search_templates(query_lower)
        
        # Search in regions (areas like sidebars, address bars)
        region_matches = self._search_regions(query_lower)
        
        # Combine and rank results
        all_matches = template_matches + region_matches
        
        if not all_matches:
            return {
                "found": False,
                "query": query,
                "error": "No matching UI elements found",
                "hint": "Try terms like: 'youtube logo', 'browser tab', 'sidebar', 'close button', 'address bar'"
            }
        
        # Sort by score (higher is better)
        all_matches.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top match
        best = all_matches[0]
        
        result = {
            "found": True,
            "query": query,
            "best_key": best["key"],
            "type": best["type"],  # "template" or "region"
            "score": round(best["score"], 3),
            "alternatives": [m["key"] for m in all_matches[1:4]]  # Show alternatives
        }
        
        return result
    
    def _search_templates(self, query: str):
        """Search through available templates"""
        matches = []
        
        for template_name in TEMPLATES.keys():
            score = self._calculate_similarity(query, template_name)
            if score > 0.2:  # Threshold to filter out poor matches
                matches.append({
                    "key": template_name,
                    "type": "template",
                    "score": score
                })
        
        return matches
    
    def _search_regions(self, query: str):
        """Search through available regions"""
        matches = []
        
        for region_name in REGION_MAP.keys():
            score = self._calculate_similarity(query, region_name)
            if score > 0.2:  # Threshold
                matches.append({
                    "key": region_name,
                    "type": "region",
                    "score": score
                })
        
        return matches
    
    def _calculate_similarity(self, query: str, target: str) -> float:
        """
        Calculate similarity score between query and target.
        Keyword-based matching with boost for exact/substring matches.
        """
        query = query.lower()
        target = target.lower()
        
        # Exact match - highest score
        if query == target:
            return 1.0
        
        # Full query appears in target
        if query in target:
            return 0.9
        
        # Target appears in query
        if target in query:
            return 0.85
        
        # Break into words and count matches
        query_words = set(query.replace("_", " ").replace("-", " ").split())
        target_words = set(target.replace("_", " ").replace("-", " ").split())
        
        # Remove common words that don't add meaning
        stop_words = {"the", "a", "an", "on", "in", "at", "to", "for", "of", "with"}
        query_words -= stop_words
        target_words -= stop_words
        
        if not query_words or not target_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words & target_words)
        union = len(query_words | target_words)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # Boost score if all query words are present
        if query_words.issubset(target_words):
            jaccard *= 1.2
        
        return min(jaccard, 1.0)  # Cap at 1.0
    
    def get_result_summary(self, result):
        """Generate human-readable summary for agent"""
        if result.get("found"):
            best_key = result.get("best_key")
            ref_type = result.get("type")
            
            if ref_type == "template":
                return f"Found template '{best_key}' - use detect_ui_elements(template='{best_key}')"
            else:
                return f"Found region '{best_key}' - use detect_ui_regions(region='{best_key}')"
        else:
            return f"No UI element found for '{result.get('query')}'. Try more specific terms."