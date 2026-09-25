import inspect
from livekit.plugins.google import utils as gutils

print(gutils.__file__)
print([n for n in dir(gutils) if "tool" in n.lower() or "schema" in n.lower() or "fnc" in n.lower()])
for name in ("create_tools_config", "to_fnc_ctx", "_build_tools", "create_tool", "get_tool_results"):
    if hasattr(gutils, name):
        print("====", name)
        print(inspect.getsource(getattr(gutils, name))[:2500])

# dump file start for function names
src = inspect.getsource(gutils)
for line in src.splitlines():
    if line.startswith("def ") or line.startswith("async def "):
        print("FN", line)
