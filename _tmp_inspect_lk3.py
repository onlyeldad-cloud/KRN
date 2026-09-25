import inspect
from livekit.agents.llm.utils import build_legacy_openai_schema, build_strict_openai_schema

print("--- build_legacy ---")
print(inspect.getsource(build_legacy_openai_schema)[:2500])
print("--- build_strict ---")
print(inspect.getsource(build_strict_openai_schema)[:2000])
