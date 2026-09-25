import inspect
from livekit.agents.llm.tool_context import FunctionTool, FunctionToolInfo
from livekit.agents.llm import utils as llm_utils
import livekit.agents.llm as llm_pkg
import os

print("llm dir", os.listdir(os.path.dirname(llm_pkg.__file__)))
print("--- FunctionTool class ---")
print(inspect.getsource(FunctionTool)[:2500])
print("--- FunctionToolInfo ---")
print(inspect.getsource(FunctionToolInfo)[:2000])

# find schema generation
for name in dir(llm_utils):
    if "schema" in name.lower() or "tool" in name.lower() or "fnc" in name.lower():
        print("utils", name)
