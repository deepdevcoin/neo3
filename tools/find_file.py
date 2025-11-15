import os
from tools import Tool, ToolCategory, ToolBehavior
class FindFile(Tool):
    name = "find_file"
    description = """Search for files by name in current directory and subdirectories.

Recursively searches from current working directory.

Input: filename (string) - Filename or partial name (case-insensitive)

Returns: found (bool), count (int), filename (search term), results (list of paths, max 50)

Use cases:
- Finding configuration files
- Locating scripts or documents
- Checking if file exists

Example: searching "config" matches "config.py", "my_config.json", etc."""
    
    args = {"filename": "string"}
    
    category = ToolCategory.SEARCH
    behavior = ToolBehavior.TERMINAL
    execution_delay = 0.0
    
    success_keys = ["found"]
    
    example_usage = """find_file(filename="config.py")
→ Searches recursively
→ Returns: {found: true, count: 2, results: ["/path/to/config.py", ...]}"""
    
    def run(self, filename: str) -> dict:
        try:
            repo_root = os.path.abspath(os.getcwd())
            filename_lower = filename.lower()
            matches = []
            
            # Walk directory tree
            for root, _, files in os.walk(repo_root):
                # Skip hidden directories and common ignore patterns
                if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.venv']):
                    continue
                
                for f in files:
                    if filename_lower in f.lower():
                        matches.append(os.path.join(root, f))
                
                # Limit to prevent hanging on large directories
                if len(matches) >= 100:
                    break
            
            return {
                "found": bool(matches),
                "count": len(matches),
                "filename": filename,
                "results": matches[:50]  # Limit results
            }
            
        except Exception as e:
            return {
                "found": False,
                "count": 0,
                "filename": filename,
                "error": str(e)
            }
    
    def get_result_summary(self, result):
        if result.get("found"):
            count = result.get("count", 0)
            return f"Found {count} file(s) matching '{result.get('filename')}'"
        return f"No files found matching '{result.get('filename')}'"

