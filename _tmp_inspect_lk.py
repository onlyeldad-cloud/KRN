import inspect

from livekit.agents import JobContext, function_tool
from livekit.agents.llm import FunctionTool
import livekit.agents.llm as llm_mod

print("llm module", llm_mod.__file__)
print("FunctionTool", FunctionTool)
print("FunctionTool attrs", [a for a in dir(FunctionTool) if not a.startswith("_")])
print("--- function_tool ---")
print(inspect.getsource(function_tool)[:4000])
print("--- wait_for_participant ---")
print(inspect.getsource(JobContext.wait_for_participant))
print("--- connect sig ---")
print(inspect.signature(JobContext.connect))
