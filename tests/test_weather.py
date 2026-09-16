from unittest.mock import AsyncMock, patch

import httpx
import pytest

from weather import get_weather


@pytest.mark.asyncio
async def test_weather_requires_a_place():
    assert (await get_weather(" "))["status"] == "invalid_location"


@pytest.mark.asyncio
async def test_unknown_place_is_not_invented():
    response = httpx.Response(
        200, json={}, request=httpx.Request("GET", "https://example.com")
    )
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=response)):
        assert (await get_weather("unknown"))["status"] == "not_found"
