import inspect
from livekit.agents.llm.tool_context import ToolContext

print("--- parse_function_tools ---")
print(inspect.getsource(ToolContext.parse_function_tools)[:2500])
print("--- init ---")
print(inspect.signature(ToolContext.__init__))
print(inspect.getsource(ToolContext.__init__)[:1500])
