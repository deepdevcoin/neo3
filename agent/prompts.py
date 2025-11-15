"""
Production system prompts - minimal and effective
"""


def build_system_prompt(tool_registry):
    """Build system prompt that guides planning"""
    
    SYSTEM_PROMPT = """You are a production-grade desktop automation agent for Pop!_OS Linux with GNOME.

# YOUR APPROACH

1. **Understand the Goal** - Parse what the user wants clearly
2. **Plan Efficiently** - Create minimal, effective step sequences
3. **Execute Safely** - Follow safety rules and dependencies
4. **Handle Failures** - Retry intelligently when steps fail

# CORE PRINCIPLES

**System State Awareness**
- ALWAYS start with `get_system_state` to understand context
- Verify the correct application is active before interacting
- Never assume UI state
    
**Search Before Detect**
- Use `retrieve_ui_reference` to find element names
- Pass the EXACT `best_key` returned to detection tools
- Don't guess template or region names

**Data Flow Integrity**
- Use EXACT values between steps (coordinates, keys, references)
- If step 1 returns `{x: 150, y: 80}`, use EXACTLY those numbers in step 2
- Don't modify, round, or estimate values

**Failure Recovery**
- Steps can retry up to 3 times automatically
- Adapt approach if repeated failures occur
- Inform user clearly if goal becomes impossible

# SAFETY RULES

1. **Rate Limiting** - System enforces delays between operations
2. **Tool Conflicts** - Some tools can't be called together (handled automatically)
3. **Overlay Usage** - ONLY use `draw_overlay` when user asks to "highlight", "show", or "mark"
4. **Simple Tasks** - Don't overcomplicate (e.g., "open browser" needs just 2 steps)

# ENVIRONMENT

- OS: Pop!_OS 22.04 LTS
- Desktop: GNOME 42.9
- Screen: 1920x1080
- Browser: Brave
- Terminal: gnome-terminal

# YOUR STYLE

- Be concise and efficient
- Create minimal plans (fewer steps = better)
- Trust the tool descriptions
- Handle errors gracefully
- Keep user informed of progress

Remember: Each tool has detailed documentation. Read it carefully and follow the patterns shown.
"""
    
    return SYSTEM_PROMPT


def print_tool_summary(tool_registry):
    """Print organized tool summary"""
    print("\n" + "="*70)
    print("🛠️  AVAILABLE TOOLS")
    print("="*70)
    
    # Group by category
    by_category = {}
    for name, tool in tool_registry.tools.items():
        cat = tool.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tool)
    
    for category in sorted(by_category.keys()):
        tools = by_category[category]
        print(f"\n📦 {category.upper()} ({len(tools)} tools)")
        print("-" * 70)
        
        for tool in sorted(tools, key=lambda t: t.name):
            # Get first sentence of description
            desc = tool.description.split('.')[0]
            if len(desc) > 60:
                desc = desc[:57] + "..."
            
            print(f"  • {tool.name:<25} {desc}")
    
    print("\n" + "="*70)
    print(f"Total: {len(tool_registry.tools)} tools available")
    print("="*70 + "\n")


def get_example_plans():
    """Example plans for common tasks"""
    return {
        "open_browser": {
            "goal": "Open Brave browser",
            "steps": [
                {
                    "step_number": 1,
                    "tool_name": "get_system_state",
                    "arguments": {},
                    "purpose": "Check current application",
                    "dependencies": []
                },
                {
                    "step_number": 2,
                    "tool_name": "keyboard_shortcut",
                    "arguments": {"action": "browser"},
                    "purpose": "Open browser with Alt+B",
                    "dependencies": [1]
                }
            ]
        },
        
        "click_element": {
            "goal": "Click YouTube logo",
            "steps": [
                {
                    "step_number": 1,
                    "tool_name": "get_system_state",
                    "arguments": {},
                    "purpose": "Verify browser is active",
                    "dependencies": []
                },
                {
                    "step_number": 2,
                    "tool_name": "retrieve_ui_reference",
                    "arguments": {"query": "youtube logo"},
                    "purpose": "Find correct template name",
                    "dependencies": [1]
                },
                {
                    "step_number": 3,
                    "tool_name": "detect_ui_elements",
                    "arguments": {"template": "<use result.best_key from step 2>"},
                    "purpose": "Get logo coordinates",
                    "dependencies": [2]
                },
                {
                    "step_number": 4,
                    "tool_name": "mouse_click",
                    "arguments": {"x": "<use result.x>", "y": "<use result.y>"},
                    "purpose": "Click the logo",
                    "dependencies": [3]
                }
            ]
        },
        
        "highlight_element": {
            "goal": "Highlight address bar",
            "steps": [
                {
                    "step_number": 1,
                    "tool_name": "retrieve_ui_reference",
                    "arguments": {"query": "address bar"},
                    "purpose": "Find address bar region",
                    "dependencies": []
                },
                {
                    "step_number": 2,
                    "tool_name": "detect_ui_regions",
                    "arguments": {"region": "<use result.best_key>"},
                    "purpose": "Get coordinates",
                    "dependencies": [1]
                },
                {
                    "step_number": 3,
                    "tool_name": "draw_overlay",
                    "arguments": {"coords": "<x1 y1 x2 y2 from step 2>"},
                    "purpose": "Draw rectangle highlight",
                    "dependencies": [2]
                }
            ]
        }
    }