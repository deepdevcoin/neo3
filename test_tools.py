#!/usr/bin/env python3
"""
Test script to verify all tools are properly configured
"""

from agent.registry import ToolRegistry
from agent.prompts import print_tool_summary

def test_tool_loading():
    """Test that all tools load correctly"""
    print("🔧 Testing tool loading...\n")
    
    registry = ToolRegistry()
    registry.load_all()
    
    print(f"✅ Loaded {len(registry.tools)} tools:\n")
    
    for name, tool in sorted(registry.tools.items()):
        print(f"  • {name}")
        
        # Check required attributes
        assert hasattr(tool, 'name'), f"{name} missing 'name' attribute"
        assert hasattr(tool, 'description'), f"{name} missing 'description' attribute"
        assert hasattr(tool, 'args'), f"{name} missing 'args' attribute"
        assert hasattr(tool, 'category'), f"{name} missing 'category' attribute"
        assert hasattr(tool, 'behavior'), f"{name} missing 'behavior' attribute"
        assert hasattr(tool, 'run'), f"{name} missing 'run' method"
        
        # Test metadata methods
        metadata = tool.get_metadata()
        assert 'name' in metadata
        assert 'description' in metadata
        assert 'category' in metadata
        assert 'behavior' in metadata
    
    print(f"\n✅ All tools loaded successfully!")
    return registry


def test_tool_metadata(registry):
    """Test tool metadata"""
    print("\n📊 Testing tool metadata...\n")
    
    from tools import ToolCategory, ToolBehavior
    
    categories = {}
    behaviors = {}
    
    for name, tool in registry.tools.items():
        # Categorize
        cat = tool.category.value
        categories[cat] = categories.get(cat, 0) + 1
        
        beh = tool.behavior.value
        behaviors[beh] = behaviors.get(beh, 0) + 1
    
    print("📦 Tools by category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count} tools")
    
    print("\n🔄 Tools by behavior:")
    for beh, count in sorted(behaviors.items()):
        print(f"  • {beh}: {count} tools")
    
    print("\n✅ Metadata test passed!")


def test_tool_execution(registry):
    """Test basic tool execution (safe tests only)"""
    print("\n🧪 Testing tool execution...\n")
    
    # Test get_mouse_position (safe to run)
    if "get_mouse_position" in registry.tools:
        print("Testing get_mouse_position...")
        result = registry.call("get_mouse_position", {})
        print(f"  Result: {result}")
        assert "success" in result or "x" in result, "get_mouse_position failed"
        print("  ✅ get_mouse_position works")
    
    # Test retrieve_ui_reference (safe to run)
    if "retrieve_ui_reference" in registry.tools:
        print("\nTesting retrieve_ui_reference...")
        result = registry.call("retrieve_ui_reference", {"query": "youtube logo"})
        print(f"  Result: {result}")
        assert "query" in result, "retrieve_ui_reference failed"
        print("  ✅ retrieve_ui_reference works")
    
    # Test find_file (safe to run)
    if "find_file" in registry.tools:
        print("\nTesting find_file...")
        result = registry.call("find_file", {"filename": "test"})
        print(f"  Result: {result}")
        assert "found" in result, "find_file failed"
        print("  ✅ find_file works")
    
    print("\n✅ Basic execution tests passed!")
    print("\n⚠️  Note: Not all tools tested to avoid unwanted actions")
    print("   (mouse clicks, keyboard input, etc.)")


def test_prompt_generation(registry):
    """Test that prompt can be generated"""
    print("\n📝 Testing prompt generation...\n")
    
    from agent.prompts import build_system_prompt
    
    prompt = build_system_prompt(registry)
    
    assert len(prompt) > 0, "Prompt is empty"
    assert "AVAILABLE TOOLS" in prompt, "Prompt missing tools section"
    assert "TOOL BEHAVIORS" in prompt, "Prompt missing behaviors section"
    
    print(f"✅ Prompt generated successfully ({len(prompt)} characters)")


def main():
    print("="*60)
    print("🧪 TOOL SYSTEM TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Load tools
        registry = test_tool_loading()
        
        # Test 2: Check metadata
        test_tool_metadata(registry)
        
        # Test 3: Execute safe tools
        test_tool_execution(registry)
        
        # Test 4: Generate prompt
        test_prompt_generation(registry)
        
        # Print summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
        print("\n📋 Tool Summary:")
        print_tool_summary(registry)
        
        print("\n🚀 System is ready to use!")
        print("\nRun: python3 main.py")
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED!")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())