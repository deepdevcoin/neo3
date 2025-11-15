"""
Core agent logic with streaming and simplified output.
"""
import json
import requests
import time
from typing import Dict, Any, Optional, List
from agent.planning import DynamicPlanner, PlanStatus
from config import MODEL_PROVIDER

class Agent:
    def __init__(
        self,
        model: str,
        api_url: str,
        tool_registry,
        system_prompt: str,
        api_key: Optional[str] = None,
        provider: str = MODEL_PROVIDER,
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
        self.planning_mode = planning_mode
        self.planner = DynamicPlanner(tool_registry)
        self.last_tool_time = 0
        print(f"Model: {model} ({provider}) | Planning: {planning_mode} | Max Iterations: {max_iterations}\n")

    def chat(self, user_message: str):
        print(f"> {user_message}\n")
        if self.planning_mode:
            self._chat_with_planning(user_message)
        else:
            self._chat_reactive(user_message)

    def _chat_with_planning(self, user_message: str):
        plan = self._generate_plan(user_message)
        if not plan:
            print("\nPlanning failed. Falling back to reactive mode.")
            self._chat_reactive(user_message)
            return
        self.planner.current_plan = plan
        plan.start()
        print(self.planner.get_plan_summary())
        self._execute_plan()
        self.planner.execution_history.append(plan)

    def _generate_plan(self, user_goal: str) -> Optional[Any]:
        planning_prompt = self.planner.create_planning_prompt(user_goal)
        planning_messages = [
            {"role": "system", "content": "You are an expert planning agent. Create optimal execution plans in JSON format."},
            {"role": "user", "content": planning_prompt}
        ]
        print("Generating plan...\n")
        try:
            response_content = ""
            print("AI: ", end="", flush=True)
            for chunk in self._call_model(planning_messages, use_tools=False, stream=True):
                response_content += chunk
                print(chunk, end="", flush=True)
            print("\n")
            if not response_content:
                print("No response from model for planning.")
                return None
            plan = self.planner.parse_plan_from_response(response_content, user_goal)
            if plan:
                print(f"Plan created with {len(plan.steps)} steps.")
            else:
                print("Failed to parse plan.")
            return plan
        except Exception as e:
            print(f"Error generating plan: {e}")
            return None

    def _execute_plan(self):
        iteration = 0
        while iteration < self.max_iterations:
            if self.planner.is_plan_complete():
                print("\n🎉 PLAN COMPLETED SUCCESSFULLY")
                self.planner.current_plan.complete()
                return
            if self.planner.is_plan_blocked():
                print("\n🚫 PLAN BLOCKED - Cannot proceed.")
                self.planner.current_plan.fail()
                return
            next_step = self.planner.get_next_executable_step()
            if not next_step:
                break
            iteration += 1
            print(f"\n--- Step {next_step.step_number}: {next_step.tool_name} ---")
            next_step.start()
            result = self._execute_tool_safe(next_step.tool_name, next_step.arguments)
            tool = self.tools.tools.get(next_step.tool_name)
            self.planner.update_step_result(next_step, result, tool)
            if next_step.status == PlanStatus.FAILED and next_step.can_retry():
                print(f"Retrying (attempt {next_step.retry_count + 1}/{next_step.max_retries})")
            time.sleep(self.min_step_delay)
        if not self.planner.is_plan_complete():
            print("\n⚠️ Plan execution finished, but not all steps were completed.")

    def _execute_tool_safe(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = time.time()
            if now - self.last_tool_time < 0.5:
                time.sleep(0.5)
            tool = self.tools.tools.get(tool_name)
            if not tool:
                return {"error": f"Tool '{tool_name}' not found"}
            print(f"Executing: {tool_name}({json.dumps(arguments)}) ", end="", flush=True)
            result = self.tools.call(tool_name, arguments)
            self.last_tool_time = time.time()
            success = tool.is_successful(result) if tool else result.get('success', False)
            print("✅" if success else "❌")
            return result
        except Exception as e:
            print(f"❌ Error executing tool: {e}")
            return {"error": str(e)}

    def _chat_reactive(self, user_message: str):
        self.history.append({"role": "user", "content": user_message})
        print("AI: ", end="", flush=True)
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            response_content = ""
            tool_calls = []
            for chunk in self._call_model(self.history, use_tools=True, stream=True):
                response_content += chunk
                print(chunk, end="", flush=True)
            # In a real streaming scenario, tool calls would be built chunk by chunk.
            # For now, we'll parse them from the complete response.
            try:
                # This is a simplification. A proper implementation would parse streaming tool calls.
                full_response = json.loads(response_content)
                tool_calls = full_response.get('tool_calls', [])
            except json.JSONDecodeError:
                pass # It's just text
            if not tool_calls:
                print()
                self.history.append({"role": "assistant", "content": response_content})
                break
            self.history.append({"role": "assistant", "content": response_content, "tool_calls": tool_calls})
            for tool_call in tool_calls:
                function_info = tool_call.get('function', {})
                tool_name = function_info.get('name')
                args_str = function_info.get('arguments', '{}')
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {}
                result = self._execute_tool_safe(tool_name, args)
                self._add_tool_result_to_history(tool_call, result)
            time.sleep(self.min_step_delay)

    def _call_model(self, messages: List[Dict], use_tools: bool = True, stream: bool = False):
        payload = {"model": self.model, "messages": messages, "temperature": 0.1, "stream": stream}
        if use_tools:
            functions = self._convert_tools_to_functions()
            if self.provider == "anthropic":
                payload["tools"] = [f["function"] for f in functions]
                payload["max_tokens"] = 4096
            else:
                payload["tools"] = functions
                payload["tool_choice"] = "auto"
        headers = self._build_headers()
        try:
            with requests.post(self.api_url, json=payload, headers=headers, stream=stream, timeout=120) as resp:
                if resp.status_code != 200:
                    print(f"HTTP Error {resp.status_code}: {resp.text}")
                    return
                if not stream:
                    data = resp.json()
                    # Non-streaming logic would go here, but we now default to streaming yields
                    return
                for line in resp.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            json_str = line_str[6:]
                            if json_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(json_str)
                                if self.provider == "anthropic":
                                    delta = data.get('delta', {})
                                    if delta.get('type') == 'text_delta':
                                        yield delta.get('text', '')
                                else: # OpenAI compatible
                                    delta = data['choices'][0]['delta']
                                    if 'content' in delta and delta['content']:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                print(f"JSON decode error on line: {line_str}")
        except Exception as e:
            print(f"Model call error: {e}")

    def _convert_tools_to_functions(self) -> List[Dict]:
        functions = []
        for name, tool in self.tools.tools.items():
            properties = {}
            required = []
            for arg_name, arg_type in getattr(tool, "args", {}).items():
                type_map = {"string": "string", "int": "integer", "float": "number", "bool": "boolean"}
                is_optional = "|null" in arg_type
                clean_type = arg_type.replace("|null", "").strip()
                if not is_optional:
                    required.append(arg_name)
                properties[arg_name] = {"type": type_map.get(clean_type, "string"), "description": f"{arg_name}"}
            functions.append({"type": "function", "function": {"name": name, "description": tool.description, "parameters": {"type": "object", "properties": properties, "required": required}}})
        return functions

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if self.api_key:
            if self.provider == "anthropic":
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _add_tool_result_to_history(self, tool_call: Dict, result: Dict):
        tool_name = tool_call.get("function", {}).get("name")
        tool_call_id = tool_call.get("id", f"call_{tool_name}")
        if self.provider == "anthropic":
            self.history.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_call_id, "content": json.dumps(result)}]})
        else:
            self.history.append({"role": "tool", "tool_call_id": tool_call_id, "name": tool_name, "content": json.dumps(result)})
