"""
Production-grade dynamic planning with retry logic and progress tracking
"""
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PlanStatus(Enum):
    """Status of plan execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    RETRYING = "retrying"


@dataclass
class PlanStep:
    """A single step in an execution plan"""
    step_number: int
    tool_name: str
    arguments: Dict[str, Any]
    purpose: str
    dependencies: List[int] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self):
        return {
            'step_number': self.step_number,
            'tool_name': self.tool_name,
            'arguments': self.arguments,
            'purpose': self.purpose,
            'dependencies': self.dependencies,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error': self.error
        }
    
    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return self.retry_count < self.max_retries and self.status == PlanStatus.FAILED
    
    def start(self):
        """Mark step as started"""
        self.status = PlanStatus.IN_PROGRESS
        self.started_at = time.time()
    
    def complete(self, result: Dict[str, Any]):
        """Mark step as completed"""
        self.status = PlanStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()
    
    def fail(self, error: str):
        """Mark step as failed"""
        self.status = PlanStatus.FAILED
        self.error = error
        self.completed_at = time.time()
    
    def retry(self):
        """Prepare step for retry"""
        self.retry_count += 1
        self.status = PlanStatus.RETRYING
        self.error = None


@dataclass
class ExecutionPlan:
    """Complete execution plan with progress tracking"""
    goal: str
    steps: List[PlanStep]
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    current_step: int = 0
    status: PlanStatus = PlanStatus.PENDING
    
    def to_dict(self):
        completed = sum(1 for s in self.steps if s.status == PlanStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == PlanStatus.FAILED)
        
        return {
            'goal': self.goal,
            'steps': [step.to_dict() for step in self.steps],
            'current_step': self.current_step,
            'status': self.status.value,
            'total_steps': len(self.steps),
            'completed_steps': completed,
            'failed_steps': failed,
            'progress': f"{completed}/{len(self.steps)}",
            'duration': self.get_duration()
        }
    
    def get_duration(self) -> Optional[float]:
        """Get execution duration"""
        if not self.started_at:
            return None
        end = self.completed_at or time.time()
        return round(end - self.started_at, 2)
    
    def start(self):
        """Mark plan as started"""
        self.status = PlanStatus.IN_PROGRESS
        self.started_at = time.time()
    
    def complete(self):
        """Mark plan as completed"""
        self.status = PlanStatus.COMPLETED
        self.completed_at = time.time()
    
    def fail(self):
        """Mark plan as failed"""
        self.status = PlanStatus.FAILED
        self.completed_at = time.time()


class DynamicPlanner:
    """
    Production-grade planner with retry logic and progress tracking
    """
    
    def __init__(self, tool_registry):
        self.tools = tool_registry
        self.current_plan: Optional[ExecutionPlan] = None
        self.execution_history: List[ExecutionPlan] = []
        
    def get_planning_context(self) -> str:
        """Generate comprehensive tool documentation"""
        context_parts = [
            "# AVAILABLE TOOLS\n",
            "You are a desktop automation agent. Below are your capabilities.\n"
        ]
        
        # Group tools by category
        categories = {}
        for name, tool in self.tools.tools.items():
            category = tool.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        # Document each category
        for category, tools in sorted(categories.items()):
            context_parts.append(f"\n## {category.upper()} TOOLS\n")
            
            for tool in sorted(tools, key=lambda t: t.name):
                context_parts.append(f"\n### {tool.name}\n")
                context_parts.append(f"{tool.description}\n")
                
                if tool.args:
                    context_parts.append("\n**Arguments:**\n")
                    for arg_name, arg_type in tool.args.items():
                        optional = " (optional)" if "|null" in arg_type else " (required)"
                        clean_type = arg_type.replace("|null", "")
                        context_parts.append(f"- {arg_name}: {clean_type}{optional}\n")
                
                if hasattr(tool, 'example_usage') and tool.example_usage:
                    context_parts.append(f"\n**Example:**\n{tool.example_usage}\n")
        
        return ''.join(context_parts)
    
    def create_planning_prompt(self, user_goal: str) -> str:
        """Create planning prompt with patterns"""
        tool_context = self.get_planning_context()
        
        return f"""{tool_context}

# YOUR TASK

**User Goal:** {user_goal}

Create a detailed step-by-step execution plan to achieve this goal.

# PLANNING RULES

1.  **Direct Action:** If the user provides all necessary information for a tool, create a one-step plan.
2.  **Multi-step:** If information is missing, create a multi-step plan to gather it before acting.
3.  **Simplicity:** Always prefer the simplest, most direct plan.

# COMMON PATTERNS

**Direct Action (all info provided):**
-   User: "draw circle at 800 900" -> Plan: `draw_overlay(coords="800 900")`
-   User: "find file 'test_vision_tools'" -> Plan: `find_file(filename="test_vision_tools")`

**Multi-step (info missing):**
-   User: "click the button"
    1.  `get_system_state()` - Check current app
    2.  `retrieve_ui_reference(query="button")` - Find button
    3.  `detect_ui_elements(template=<result.best_key>)` - Get coordinates
    4.  `mouse_click(x=<result.x>, y=<result.y>)` - Click it

# OUTPUT FORMAT

Return ONLY valid JSON (no markdown):

```json
{{
  "reasoning": "Brief explanation of approach",
  "steps": [
    {{
      "step_number": 1,
      "tool_name": "tool_name",
      "arguments": {{"arg": "value"}},
      "purpose": "Do something",
      "dependencies": []
    }}
  ]
}}
```

**CRITICAL:**
-   Output ONLY JSON.
-   `draw_overlay` should only be used when the user explicitly asks to "highlight", "show", or "mark".
-   Keep plans minimal and efficient.

Create the plan for: **{user_goal}**
"""
    
    def parse_plan_from_response(self, response: str, goal: str) -> Optional[ExecutionPlan]:
        """Parse JSON plan from model response"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                # Remove first line and last line
                response = '\n'.join(lines[1:-1])
                # Remove any remaining json markers
                response = response.replace('```json', '').replace('```', '')
            
            # Parse JSON
            plan_data = json.loads(response)
            
            if 'steps' not in plan_data:
                print("❌ Plan missing 'steps' field")
                return None
            
            # Create PlanStep objects
            steps = []
            for step_data in plan_data['steps']:
                step = PlanStep(
                    step_number=step_data.get('step_number', len(steps) + 1),
                    tool_name=step_data['tool_name'],
                    arguments=step_data.get('arguments', {}),
                    purpose=step_data.get('purpose', ''),
                    dependencies=step_data.get('dependencies', [])
                )
                steps.append(step)
            
            # Validate dependencies
            for step in steps:
                for dep in step.dependencies:
                    if dep < 1 or dep > len(steps):
                        print(f"⚠️ Step {step.step_number} has invalid dependency: {dep}")
                        step.dependencies = [d for d in step.dependencies if 1 <= d <= len(steps)]
            
            plan = ExecutionPlan(goal=goal, steps=steps)
            return plan
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response preview: {response[:300]}")
            return None
        except Exception as e:
            print(f"❌ Error parsing plan: {e}")
            return None
    
    def get_next_executable_step(self) -> Optional[PlanStep]:
        """Get next step ready for execution"""
        if not self.current_plan:
            return None
        
        for step in self.current_plan.steps:
            # Skip completed, failed, or in-progress
            if step.status in [PlanStatus.COMPLETED, PlanStatus.IN_PROGRESS]:
                continue
            
            # Check if this is a retry candidate
            if step.status == PlanStatus.FAILED:
                if step.can_retry():
                    return step
                else:
                    continue  # Skip failed steps that can't retry
            
            # Check dependencies
            dependencies_met = all(
                self.current_plan.steps[dep - 1].status == PlanStatus.COMPLETED
                for dep in step.dependencies
                if 0 < dep <= len(self.current_plan.steps)
            )
            
            if dependencies_met:
                return step
        
        return None
    
    def update_step_result(self, step: PlanStep, result: Dict[str, Any], tool):
        """Update step with execution result"""
        if tool and tool.is_successful(result):
            step.complete(result)
            print(f"  ✅ Step {step.step_number} completed: {step.purpose}")
        else:
            error_msg = result.get('error', 'Tool execution failed')
            step.fail(error_msg)
            print(f"  ❌ Step {step.step_number} failed: {error_msg}")
            
            if step.can_retry():
                print(f"  🔄 Will retry (attempt {step.retry_count + 1}/{step.max_retries})")
    
    def is_plan_complete(self) -> bool:
        """Check if all steps completed"""
        if not self.current_plan:
            return False
        return all(s.status == PlanStatus.COMPLETED for s in self.current_plan.steps)
    
    def is_plan_blocked(self) -> bool:
        """Check if plan is blocked"""
        if not self.current_plan:
            return False
        
        # Check for failed steps with exhausted retries
        failed_steps = [
            s.step_number for s in self.current_plan.steps 
            if s.status == PlanStatus.FAILED and not s.can_retry()
        ]
        
        if failed_steps:
            # Check if any pending steps depend on failed steps
            for step in self.current_plan.steps:
                if step.status in [PlanStatus.PENDING, PlanStatus.RETRYING]:
                    if any(dep in failed_steps for dep in step.dependencies):
                        return True
        
        # Check if we have pending steps but none are executable
        has_pending = any(
            s.status in [PlanStatus.PENDING, PlanStatus.RETRYING] 
            for s in self.current_plan.steps
        )
        has_executable = self.get_next_executable_step() is not None
        
        return has_pending and not has_executable
    
    def get_plan_summary(self) -> str:
        """Get readable plan summary"""
        if not self.current_plan:
            return "No active plan"
        
        lines = [
            f"\n{'='*70}",
            f"📋 EXECUTION PLAN: {self.current_plan.goal}",
            f"{'='*70}\n"
        ]
        
        status_icons = {
            PlanStatus.COMPLETED: "✅",
            PlanStatus.IN_PROGRESS: "🔄",
            PlanStatus.FAILED: "❌",
            PlanStatus.PENDING: "⏳",
            PlanStatus.BLOCKED: "🚫",
            PlanStatus.RETRYING: "🔄"
        }
        
        for step in self.current_plan.steps:
            icon = status_icons.get(step.status, "❓")
            
            args_str = json.dumps(step.arguments) if step.arguments else "{}"
            lines.append(f"{icon} Step {step.step_number}: {step.tool_name}({args_str})")
            lines.append(f"   Purpose: {step.purpose}")
            
            if step.dependencies:
                lines.append(f"   Depends on: {', '.join(map(str, step.dependencies))}")
            
            if step.retry_count > 0:
                lines.append(f"   Retries: {step.retry_count}/{step.max_retries}")
            
            if step.status == PlanStatus.FAILED and step.error:
                lines.append(f"   Error: {step.error}")
            
            lines.append("")
        
        # Progress summary
        completed = sum(1 for s in self.current_plan.steps if s.status == PlanStatus.COMPLETED)
        failed = sum(1 for s in self.current_plan.steps if s.status == PlanStatus.FAILED)
        total = len(self.current_plan.steps)
        
        lines.append(f"Progress: {completed}/{total} completed, {failed} failed")
        
        duration = self.current_plan.get_duration()
        if duration:
            lines.append(f"Duration: {duration}s")
        
        lines.append("")
        
        return '\n'.join(lines)