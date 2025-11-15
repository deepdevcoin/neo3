"""
Production-grade configuration with safety controls
"""
import os
import pyautogui

# =====================================================
# SAFETY SETTINGS - PREVENT SYSTEM CRASHES
# =====================================================
# PyAutoGUI Safety
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.8  # Minimum delay between pyautogui calls
pyautogui.MINIMUM_DURATION = 0.2  # Smooth mouse movements
pyautogui.MINIMUM_SLEEP = 0.1  # Sleep after each action

# =====================================================
# RATE LIMITING
# =====================================================
# Prevent X11/GNOME overload
MIN_DELAY_BETWEEN_TOOLS = 0.5  # Seconds between any tool calls
MIN_DELAY_BETWEEN_STEPS = 1.0  # Seconds between plan steps
MAX_RETRIES_PER_STEP = 3  # Retry failed steps
RETRY_DELAY = 2.0  # Seconds before retry

# Overlay safety
OVERLAY_ENABLED = True  # Set to False to disable all overlays
OVERLAY_SPAWN_DELAY = 2.0  # Wait before spawning overlay process
OVERLAY_TIMEOUT = 10.0  # Kill overlay if unresponsive

# Vision system
SCREENSHOT_COOLDOWN = 0.3  # Minimum seconds between screenshots
TEMPLATE_MATCH_CACHE_TTL = 2.0  # Cache detection results

# =====================================================
# MODEL PROVIDER CONFIGURATION
# =====================================================
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "ollama")

# =====================================================
# OLLAMA CONFIGURATION
# =====================================================
OLLAMA_CONFIG = {
    "model": os.environ.get("OLLAMA_MODEL", "qwen2.5:3b-instruct"),
    "api_url": os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions"),
    "api_key": None,
}

# =====================================================
# LM STUDIO CONFIGURATION
# =====================================================
LMSTUDIO_CONFIG = {
    "model": os.environ.get("LMSTUDIO_MODEL", "local-model"),
    "api_url": os.environ.get("LMSTUDIO_API_URL", "http://localhost:1234/v1/chat/completions"),
    "api_key": None,
}

# =====================================================
# GROQ CONFIGURATION
# =====================================================
GROQ_CONFIG = {
    "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "api_url": "https://api.groq.com/openai/v1/chat/completions",
    "api_key": os.environ.get("GROQ_API_KEY"),
}

# =====================================================
# OPENAI CONFIGURATION
# =====================================================
OPENAI_CONFIG = {
    "model": os.environ.get("OPENAI_MODEL", "gpt-4-turbo-preview"),
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": os.environ.get("OPENAI_API_KEY", ""),
}

# =====================================================
# ANTHROPIC CONFIGURATION
# =====================================================
ANTHROPIC_CONFIG = {
    "model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    "api_url": "https://api.anthropic.com/v1/messages",
    "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
}

# =====================================================
# OPENROUTER CONFIGURATION
# =====================================================
OPENROUTER_CONFIG = {
    "model": os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
    "api_url": "https://openrouter.ai/api/v1/chat/completions",
    "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
}

# =====================================================
# MODEL SELECTION
# =====================================================
PROVIDER_CONFIGS = {
    "ollama": OLLAMA_CONFIG,
    "lmstudio": LMSTUDIO_CONFIG,
    "groq": GROQ_CONFIG,
    "openai": OPENAI_CONFIG,
    "anthropic": ANTHROPIC_CONFIG,
    "openrouter": OPENROUTER_CONFIG,
}

if MODEL_PROVIDER not in PROVIDER_CONFIGS:
    print(f"⚠️ Unknown provider '{MODEL_PROVIDER}', defaulting to 'groq'")
    MODEL_PROVIDER = "groq"

current_config = PROVIDER_CONFIGS[MODEL_PROVIDER]

MODEL = current_config["model"]
API_URL = current_config["api_url"]
API_KEY = current_config["api_key"]

# =====================================================
# AGENT SETTINGS
# =====================================================
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "20"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.1"))
PLANNING_ENABLED = True

# =====================================================
# DEBUG SETTINGS
# =====================================================
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
VERBOSE_LOGGING = os.environ.get("VERBOSE_LOGGING", "false").lower() == "true"
SAVE_DEBUG_SCREENSHOTS = True

# =====================================================
# SYSTEM INFO
# =====================================================
SYSTEM_INFO = {
    "os": "Pop!_OS 22.04 LTS",
    "de": "GNOME 42.9",
    "wm": "Mutter",
    "resolution": "1920x1080",
    "default_browser": "Brave",
    "terminal": "gnome-terminal",
}

# =====================================================
# DEBUG INFO
# =====================================================
def print_config():
    print("\n" + "="*60)
    print("🤖 PRODUCTION AGENT CONFIGURATION")
    print("="*60)
    print(f"Provider: {MODEL_PROVIDER}")
    print(f"Model: {MODEL}")
    print(f"API URL: {API_URL}")
    print(f"API Key: {'***' + API_KEY[-4:] if API_KEY else 'None'}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Planning: {'ENABLED' if PLANNING_ENABLED else 'DISABLED'}")
    print(f"Overlay: {'ENABLED' if OVERLAY_ENABLED else 'DISABLED'}")
    print(f"Safety Delays: {MIN_DELAY_BETWEEN_TOOLS}s (tools), {MIN_DELAY_BETWEEN_STEPS}s (steps)")
    print(f"Max Retries: {MAX_RETRIES_PER_STEP}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print("="*60 + "\n")