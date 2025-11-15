# Scalable Agentic System - Setup Instructions

## 📁 Directory Structure

```
neo3/
├── agent/
│   ├── __init__.py
│   ├── core.py              # Metadata-driven agent loop
│   ├── prompts.py           # Dynamic prompt builder
│   └── registry.py          # Tool registry (keep your existing one)
│
├── tools/
│   ├── __init__.py          # Enhanced Tool base class
│   ├── keyboard_shortcuts.py
│   ├── draw_overlay.py
│   ├── detect_text.py
│   ├── find_file.py
│   ├── retrieve_ui_reference.py
│   └── vision_tools.py
│
├── vision/
│   ├── vision.py
│   ├── regions.py
│   └── region_assignments.py
│
├── overlay/
│   ├── overlay_manager.py
│   ├── overlay_process.py
│   └── overlay_window.py
│
├── templates/              # Your UI template images
│
├── main.py                 # Entry point
│
└── requirements.txt
```

## 🔧 Migration Steps

### 1. Create agent directory
```bash
mkdir -p agent
```

### 2. Update files

Replace these files with the new versions:
- `agent/__init__.py` (empty or imports)
- `agent/core.py` (new agentic loop)
- `agent/prompts.py` (dynamic prompt builder)
- `tools/__init__.py` (enhanced Tool base)
- `main.py` (new entry point)

Update these tool files with metadata:
- `tools/keyboard_shortcuts.py`
- `tools/draw_overlay.py`
- `tools/detect_text.py`
- `tools/find_file.py`
- `tools/retrieve_ui_reference.py`
- `tools/vision_tools.py`

### 3. Keep your existing files
- `agent/registry.py` (your existing tool registry)
- `vision/*` (all vision files)
- `overlay/*` (all overlay files)
- `templates/*` (your UI templates)

## 📝 Adding New Tools (100% Scalable)

To add a new tool, just create a file in `tools/` with this pattern:

```python
from tools import Tool, ToolCategory, ToolBehavior

class YourNewTool(Tool):
    name = "your_tool_name"
    description = "What this tool does - used in prompt generation"
    args = {"param1": "string", "param2": "int"}
    
    # Metadata
    category = ToolCategory.ACTION  # or DETECTION, SEARCH, RETRIEVAL
    behavior = ToolBehavior.TERMINAL  # or INTERMEDIATE, REQUIRES_FOLLOWUP
    execution_delay = 0.5  # seconds to wait after execution
    
    # Result interpretation
    success_keys = ["success", "found"]
    failure_keys = ["error"]
    
    # Optional: custom result summary
    result_summary_template = "Action completed: {result_field}"
    
    # Optional: for REQUIRES_FOLLOWUP behavior
    followup_suggestions = ["tool_to_call_next"]
    
    def run(self, param1, param2):
        # Your tool logic
        return {
            "success": True,
            "result_field": "some value"
        }
```

**That's it!** The system will:
- ✅ Auto-discover the tool
- ✅ Add it to the prompt automatically
- ✅ Use its metadata for flow control
- ✅ Apply execution delays
- ✅ Handle success/failure detection
- ✅ Generate result summaries

## 🎯 Tool Behavior Types

### TERMINAL
- Task ends after this tool
- Example: `draw_overlay`, `find_file`, `detect_text`

### INTERMEDIATE
- Agent continues if successful, stops if failed
- Example: `keyboard_shortcut`, `detect_ui_elements`

### REQUIRES_FOLLOWUP
- MUST be followed by another tool
- Specify `followup_suggestions`
- Example: `retrieve_ui_reference` → must call `detect_ui_elements`

## 🚀 Running the System

```bash
python3 main.py
```

## 📊 Tool Categories

### ACTION
Tools that execute actions (keyboard, mouse, overlays)

### DETECTION
Tools that find things on screen (OCR, template matching)

### SEARCH
Tools that search for files or data

### RETRIEVAL
Tools that look up information (knowledge bases, references)

### SYSTEM
System-level operations

## 🔄 How It Works

1. **Tool Discovery**: Registry auto-loads all Tool subclasses
2. **Prompt Generation**: Prompts built dynamically from tool metadata
3. **Agentic Loop**: Agent uses metadata to decide when to stop/continue
4. **Execution**: Delays and result handling driven by metadata
5. **Context**: Agent automatically tracks coordinates and references

## 💡 Benefits

- ✅ **Zero Hardcoding**: Add tools without touching core logic
- ✅ **Automatic Prompts**: Tool descriptions go straight into prompts
- ✅ **Smart Flow Control**: Metadata determines execution flow
- ✅ **Scalable**: Add 100+ tools with same pattern
- ✅ **Type Safety**: Metadata is structured and validated
- ✅ **Context Aware**: Agent tracks state automatically

## 🎓 Example Tool Addition

Want to add a "click" tool?

```python
# tools/mouse_click.py
from tools import Tool, ToolCategory, ToolBehavior
import pyautogui

class MouseClick(Tool):
    name = "mouse_click"
    description = "Click at specific coordinates on screen"
    args = {"x": "int", "y": "int"}
    
    category = ToolCategory.ACTION
    behavior = ToolBehavior.TERMINAL
    execution_delay = 0.3
    
    result_summary_template = "Clicked at ({x}, {y})"
    
    def run(self, x, y):
        pyautogui.click(x, y)
        return {"success": True, "x": x, "y": y}
```

**Done!** The agent now knows about clicking and when to use it.