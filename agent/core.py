"""
Production-grade agent with safety controls and retry logic
"""
import json
import requests
import time
from typing import Dict, Any, Optional, List
from agent.planning import DynamicPlanner, PlanStatus


class Agent:
    def __init__(
        self,
        model: str,
        api_url: str,
        tool_registry,
        system_prompt: str,
        api_key: Optional[str] = None,
        provider: str = "groq",
        max_iterations: int = 20,
        planning_mode: bool = True,
        min_step_delay: float = 1.0,
        max_retries: int = 3,
    ):
        self.model = model
        self.api_url = api_url
        self.api_key = api_key
        self.provider = provider
        self.tools = tool_registry
        self.base_system_prompt = system_prompt
        self.history: List[Dict[str, Any]] = []
        self.max_iterations = max_iterations
        self.min_step_delay = min_step_delay
        self.max_retries = max_retries
        
        # Planning
        self.planning_mode = planning_mode
        self.planner = DynamicPlanner(tool_registry)
        
        # Safety tracking
        self.last_tool_time = 0
        self.last_screenshot_time = 0
        self.tool_call_count = 0
        
        print(f"Model: {model}")
        print(f"Provider: {provider}")
        print(f"Planning: {'ENABLED' if planning_mode else 'DISABLED'}")
        print(f"Max Iterations: {max_iterations}")
        print(f"Min Step Delay: {min_step_delay}s")
        print(f"Max Retries: {max_retries}")
        print(f"{'_'*70}\n")

    def chat(self, user_message: str):
        """Main entry point"""
        print(f"USER: {user_message}")
        print(f"{'_'*70}\n")
        
        if self.planning_mode:
            self._chat_with_planning(user_message)
        else:
            self._chat_reactive(user_message)
    
    def _chat_with_planning(self, user_message: str):
        """Planning mode with retry logic"""
        print("Phase 1: PLANNING\n")
        
        plan = self._generate_plan(user_message)
        
        if not plan:
            print("❌ Planning failed. Falling back to reactive mode.")
            self._chat_reactive(user_message)
            return
        
        self.planner.current_plan = plan
        plan.start()
        
        print(self.planner.get_plan_summary())
        
        print("\nPhase 2: EXECUTION\n")
        self._execute_plan()
        
        # Save to history
        self.planner.execution_history.append(plan)
    
    def _generate_plan(self, user_goal: str) -> Optional[Any]:
        """Generate execution plan"""
        planning_prompt = self.planner.create_planning_prompt(user_goal)
        
        planning_messages = [
            {
                "role": "system",
                "content": "You are an expert planning agent. Create optimal execution plans in JSON format."
            },
            {
                "role": "user",
                "content": planning_prompt
            }
        ]
        
        print("📝 Requesting plan from model...\n")
        
        try:
            response = self._call_model(planning_messages, use_tools=False)
            
            if not response or not response.get('content'):
                print("❌ No response from model")
                return None
            
            content = response['content']
            print(f"📄 Received plan ({len(content)} chars)\n")
            
            plan = self.planner.parse_plan_from_response(content, user_goal)
            
            if plan:
                print(f"✅ Plan created with {len(plan.steps)} steps\n")
            else:
                print("❌ Failed to parse plan\n")
            
            return plan
            
        except Exception as e:
            print(f"❌ Error generating plan: {e}")
            return None
    
    def _execute_plan(self):
        """Execute plan with retry logic"""
        iteration = 0
        consecutive_failures = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Check completion
            if self.planner.is_plan_complete():
                self.planner.current_plan.complete()
                print("🎉 PLAN COMPLETED SUCCESSFULLY")
                print("_"*70)
                print(self.planner.get_plan_summary())
                return
            
            # Check if blocked
            if self.planner.is_plan_blocked():
                self.planner.current_plan.fail()
                print("\n" + '_'*70)
                print("🚫 PLAN BLOCKED - Cannot proceed")
                print('_'*70)
                print(self.planner.get_plan_summary())
                return
            
            # Get next step
            next_step = self.planner.get_next_executable_step()
            
            if not next_step:
                print("\n⚠️ No executable steps remaining")
                print(self.planner.get_plan_summary())
                return
            
            # Display progress
            print(f"\n{'_'*70}")
            print(f"⚙️ Iteration {iteration}/{self.max_iterations}")
            print(f"{'_'*70}")
            print(f"Step {next_step.step_number}: {next_step.tool_name}")
            print(f"Purpose: {next_step.purpose}")
            print(f"Arguments: {json.dumps(next_step.arguments, indent=2)}")
            
            if next_step.retry_count > 0:
                print(f"🔄 Retry attempt {next_step.retry_count}/{next_step.max_retries}")
            
            print()
            
            # Mark as in progress
            next_step.start()
            
            # Execute with safety delay
            result = self._execute_tool_safe(
                next_step.tool_name,
                next_step.arguments
            )
            
            # Get tool for validation
            tool = self.tools.tools.get(next_step.tool_name)
            
            # Update step
            self.planner.update_step_result(next_step, result, tool)
            
            # Track failures
            if next_step.status == PlanStatus.FAILED:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print("\n⚠️ 3 consecutive failures - pausing for 5 seconds")
                    time.sleep(5)
                    consecutive_failures = 0
            else:
                consecutive_failures = 0
            
            # Mandatory step delay (safety)
            if iteration < self.max_iterations:
                print(f"⏳ Safety delay: {self.min_step_delay}s...\n")
                time.sleep(self.min_step_delay)
            
            # Tool-specific delay
            if tool and hasattr(tool, 'execution_delay'):
                if tool.execution_delay > 0:
                    time.sleep(tool.execution_delay)
        
        print(f"\n⚠️ Reached maximum iterations ({self.max_iterations})")
        print(self.planner.get_plan_summary())
    
    def _execute_tool_safe(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with safety controls"""
        try:
            # Rate limiting
            now = time.time()
            time_since_last = now - self.last_tool_time
            
            if time_since_last < 0.5:
                sleep_time = 0.5 - time_since_last
                print(f"⏳ Rate limit: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            # Get tool
            tool = self.tools.tools.get(tool_name)
            
            if not tool:
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "success": False
                }
            
            # Pre-execution delay for critical tools
            critical_delays = {
                "keyboard_shortcut": 0.8,
                "mouse_click": 0.6,
                "draw_overlay": 1.5,
                "get_system_state": 0.4,
            }
            
            pre_delay = critical_delays.get(tool_name, 0.2)
            time.sleep(pre_delay)
            
            # Execute
            print(f"🔧 Executing: {tool_name}")
            result = self.tools.call(tool_name, arguments)
            
            self.last_tool_time = time.time()
            self.tool_call_count += 1
            
            # Display result
            if result:
                success = tool.is_successful(result) if tool else result.get('success', False)
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"{status}")
                
                # Show key results
                if 'found' in result:
                    print(f"  Found: {result['found']}")
                if 'x' in result and 'y' in result:
                    print(f"  Coordinates: ({result['x']}, {result['y']})")
                if 'error' in result:
                    print(f"  Error: {result['error']}")
            
            print()
            
            return result
            
        except Exception as e:
            print(f"❌ Error executing tool: {e}\n")
            return {
                "error": str(e),
                "success": False
            }
    
    def _chat_reactive(self, user_message: str):
        """Reactive mode (no planning)"""
        self.history.append({"role": "user", "content": user_message})
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n{'_'*70}")
            print(f"Iteration {iteration}/{self.max_iterations}")
            print(f"{'_'*70}\n")
            
            response = self._call_model(self.history, use_tools=True)
            
            if not response:
                print("No response from model")
                break
            
            tool_calls = response.get('tool_calls', [])
            content = response.get('content')
            
            if not tool_calls:
                if content:
                    print(f"Assistant: {content}\n")
                break
            
            # Execute tools
            for tool_call in tool_calls:
                tool_name = tool_call.get('function', {}).get('name')
                args_str = tool_call.get('function', {}).get('arguments', '{}')
                
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except:
                    args = {}
                
                print(f"Calling: {tool_name}({json.dumps(args)})")
                result = self._execute_tool_safe(tool_name, args)
                
                self._add_tool_result_to_history(tool_call, result)
            
            # Safety delay
            time.sleep(self.min_step_delay)
        
        if iteration >= self.max_iterations:
            print(f"\n⚠️ Reached maximum iterations")
    
    def _call_model(self, messages: List[Dict], use_tools: bool = True) -> Optional[Dict[str, Any]]:
        """Call LLM with error handling"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
            }
            
            if use_tools:
                functions = self._convert_tools_to_functions()
                if self.provider == "anthropic":
                    payload["tools"] = [f["function"] for f in functions]
                    payload["max_tokens"] = 4096
                else:
                    payload["tools"] = functions
                    payload["tool_choice"] = "auto"
            
            headers = self._build_headers()
            
            resp = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=120
            )
            
            if resp.status_code != 200:
                print(f"❌ HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            
            data = resp.json()
            
            if self.provider == "anthropic":
                return self._parse_anthropic_response(data)
            else:
                return self._parse_openai_response(data)
                
        except Exception as e:
            print(f"❌ Error calling model: {e}")
            return None
    
    def _parse_openai_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAI-style response"""
        choices = data.get("choices", [])
        if not choices:
            return {"tool_calls": [], "content": None}
        
        message = choices[0].get("message", {})
        return {
            "tool_calls": message.get("tool_calls", []),
            "content": message.get("content")
        }
    
    def _parse_anthropic_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Anthropic-style response"""
        content_blocks = data.get("content", [])
        
        tool_calls = []
        text_content = []
        
        for block in content_blocks:
            if block.get("type") == "text":
                text_content.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": json.dumps(block.get("input", {}))
                    }
                })
        
        return {
            "tool_calls": tool_calls,
            "content": "\n".join(text_content) if text_content else None
        }
    
    def _convert_tools_to_functions(self) -> List[Dict]:
        """Convert tools to function format"""
        functions = []
        
        for name, tool in self.tools.tools.items():
            properties = {}
            required = []
            
            for arg_name, arg_type in getattr(tool, "args", {}).items():
                type_map = {
                    "string": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean"
                }
                
                is_optional = "|null" in arg_type
                clean_type = arg_type.replace("|null", "").strip()
                
                if not is_optional:
                    required.append(arg_name)
                
                properties[arg_name] = {
                    "type": type_map.get(clean_type, "string"),
                    "description": f"{arg_name} parameter"
                }
            
            functions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        
        return functions
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers"""
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            if self.provider == "anthropic":
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _add_tool_result_to_history(self, tool_call: Dict, result: Dict):
        """Add tool result to conversation history"""
        tool_name = tool_call.get("function", {}).get("name")
        tool_call_id = tool_call.get("id", f"call_{tool_name}")
        
        if self.provider == "anthropic":
            self.history.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": json.dumps(result)
                }]
            })
        else:
            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": json.dumps(result)
            })