"""Tests that any externally provided event loop policy remains unaltered."""
import asyncio

import pytest


@pytest.mark.asyncio
async def test_uses_loop_provided_by_custom_policy(original_loop):
    """Asserts that test cases use the event loop
    provided by the custom event loop policy"""
    assert type(original_loop(asyncio.get_event_loop())).__name__ == "TestEventLoop"


@pytest.mark.asyncio
async def test_custom_policy_is_not_overwritten(original_loop):
    """Asserts that any custom event loop policy stays the same across test cases"""
    assert type(original_loop(asyncio.get_event_loop())).__name__ == "TestEventLoop"
