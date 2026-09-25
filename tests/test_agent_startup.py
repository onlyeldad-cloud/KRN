"""Startup path must stay cheap enough to join the room within 10s."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

from agent import Assistant, my_agent, prewarm, prewarm_tool_schemas
from krn_docs import prewarm_krn_docs, search_krn_docs


def test_job_entry_connects_before_session_start():
    source = inspect.getsource(my_agent)
    assert source.index("await ctx.connect()") < source.index("await session.start(")
    assert "room disconnected while waiting for participant" in source


def test_prewarm_schemas_index_and_agent_do_not_explode():
    loaded = prewarm_krn_docs()
    assert loaded > 0
    assistant = Assistant()
    schemas = prewarm_tool_schemas(assistant)
    assert schemas >= 1
    names = {getattr(tool, "__name__", "") for tool in assistant.tools}
    assert "search_krn_docs" in names
    prewarm(MagicMock())
    assert search_krn_docs.__name__ == "search_krn_docs"
