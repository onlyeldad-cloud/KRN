import inspect
from livekit.agents import job as job_mod

# find wait_for_participant helper
src = inspect.getsource(job_mod)
for i, line in enumerate(src.splitlines()):
    if "wait_for_participant" in line or "disconnected" in line.lower():
        print(f"{i}: {line}")

print("==== helper ====")
# likely in utils
import livekit.agents.utils as utils
print([n for n in dir(utils) if "wait" in n.lower() or "participant" in n.lower()])
