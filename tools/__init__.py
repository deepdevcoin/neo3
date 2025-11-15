from typing import Dict, Any, Callable, Optional, List
from enum import Enum


class ToolCategory(Enum):
    """Tool categories for better organization"""
    ACTION = "action"  # Executes immediate actions
    DETECTION = "detection"  # Finds things on screen
    SEARCH = "search"  # Searches for files/data
    RETRIEVAL = "retrieval"  # Looks up information
    SYSTEM = "system"  # System operations


class ToolBehavior(Enum):
    """Defines how the tool affects agent flow"""
    TERMINAL = "terminal"  # Task complete after this tool
    INTERMEDIATE = "intermediate"  # Continue to next step
    REQUIRES_FOLLOWUP = "requires_followup"  # Must be followed by another specific tool


class Tool:
    """Base tool class with metadata for agentic behavior"""
    
    name: str = None
    description: str = ""
    args: Dict[str, str] = {}
    
    # Metadata for agentic behavior
    category: ToolCategory = ToolCategory.ACTION
    behavior: ToolBehavior = ToolBehavior.TERMINAL
    
    # Execution metadata
    execution_delay: float = 0.0  # Seconds to wait after execution
    
    # Result interpretation
    success_keys: List[str] = ["success", "found", "ok"]  # Keys that indicate success
    failure_keys: List[str] = ["error"]  # Keys that indicate failure
    
    # For tools that require follow-up
    followup_suggestions: List[str] = []  # Suggested tools to call next
    
    # Result summary template (uses {key} placeholders)
    result_summary_template: Optional[str] = None
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool - must be implemented by subclass"""
        raise NotImplementedError()
    
    def is_successful(self, result: Dict[str, Any]) -> bool:
        """Determine if the tool execution was successful"""
        for key in self.success_keys:
            if key in result and result[key]:
                return True
        
        for key in self.failure_keys:
            if key in result:
                return False
        
        return True  # Default to success if no clear indicator
    
    def get_result_summary(self, result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the tool result"""
        if self.result_summary_template:
            try:
                return self.result_summary_template.format(**result)
            except (KeyError, ValueError):
                pass
        
        # Fallback: generic summary
        if self.is_successful(result):
            return f"{self.name} executed successfully"
        else:
            error = result.get("error", "unknown error")
            return f"{self.name} failed: {error}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata for agent reasoning"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "behavior": self.behavior.value,
            "execution_delay": self.execution_delay,
            "followup_suggestions": self.followup_suggestions
        }