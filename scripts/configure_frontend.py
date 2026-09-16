"""Copy only server credentials into the local frontend; never print secrets."""

import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key

root = Path(__file__).resolve().parents[1]
values = dotenv_values(root / ".env.local")
destination = root / "frontend" / ".env.local"
destination.touch(exist_ok=True)
for key in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"):
    if not values.get(key):
        raise SystemExit(f"Missing {key} in .env.local")
    set_key(str(destination), key, values[key])
existing = dotenv_values(destination)
dev_token = existing.get("KRN_MOBILE_DEV_TOKEN") or secrets.token_urlsafe(32)
set_key(str(destination), "KRN_MOBILE_DEV_TOKEN", dev_token)
set_key(str(destination), "AGENT_NAME", "my-agent")
mobile = root / "mobile" / "assets" / ".env"
mobile.touch(exist_ok=True)
set_key(str(mobile), "KRN_MOBILE_DEV_TOKEN", dev_token)
if not dotenv_values(mobile).get("KRN_TOKEN_ENDPOINT"):
    set_key(str(mobile), "KRN_TOKEN_ENDPOINT", "http://10.0.2.2:3000/api/token")
print(
    "Configured server credentials and a separate personal mobile development token. No secrets printed."
)
