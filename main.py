"""
Production-grade agent entry point
"""
import sys
import signal
from agent.registry import ToolRegistry
from agent.prompts import build_system_prompt, print_tool_summary
from agent.core import Agent
from config import (
    MODEL, API_URL, API_KEY, MODEL_PROVIDER,
    MAX_ITERATIONS, MIN_DELAY_BETWEEN_STEPS,
    MAX_RETRIES_PER_STEP, PLANNING_ENABLED,
    print_config
)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n👋 Shutting down gracefully...")
    
    # Close overlay if active
    try:
        from overlay.overlay_manager import manager
        manager.close()
    except:
        pass
    
    print("Goodbye!")
    sys.exit(0)


def main():
    """Main entry point"""
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print config
    print_config()
    
    # Load tools
    print("📦 Loading tools...")
    tools = ToolRegistry()
    tools.load_all()
    
    # print(f"\n")
    
    # Print tool summary
    # print_tool_summary(tools)
    
    # Build system prompt
    system_prompt = build_system_prompt(tools)
    
    # Create agent
    agent = Agent(
        model=MODEL,
        api_url=API_URL,
        tool_registry=tools,
        system_prompt=system_prompt,
        api_key=API_KEY,
        provider=MODEL_PROVIDER,
        max_iterations=MAX_ITERATIONS,
        planning_mode=PLANNING_ENABLED,
        min_step_delay=MIN_DELAY_BETWEEN_STEPS,
        max_retries=MAX_RETRIES_PER_STEP,
    )
    
    print("  'quit' or 'exit' - Stop the agent")
    print("  'stats' - Show tool usage statistics")
    print("  'tools' - Show available tools")
    print("  'toggle planning' - Switch planning mode")
    print("  'disable overlay' - Disable overlay system")
    print("="*70 + "\n")
    
    # Main loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ("quit", "exit"):
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "stats":
                stats = tools.get_stats()
                print(f"\n📊 Tool Statistics:")
                print(f"  Total calls: {stats['total_calls']}")
                print(f"  Unique tools used: {stats['unique_tools']}")
                print(f"  Top tools:")
                for tool, count in stats['top_tools']:
                    print(f"    - {tool}: {count} calls")
                continue
            
            if user_input.lower() == "tools":
                print_tool_summary(tools)
                continue
            
            if user_input.lower() == "toggle planning":
                agent.planning_mode = not agent.planning_mode
                mode = "ENABLED" if agent.planning_mode else "DISABLED"
                print(f"\n🔄 Planning mode: {mode}")
                continue
            
            if user_input.lower() == "disable overlay":
                from overlay.overlay_manager import manager
                manager.disable()
                continue
            
            if user_input.lower() == "enable overlay":
                from overlay.overlay_manager import manager
                manager.enable()
                continue
            
            # Process user request
            agent.chat(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    try:
        from overlay.overlay_manager import manager
        manager.close()
    except:
        pass
    
    print("\n✅ Agent stopped")


if __name__ == "__main__":
    main()