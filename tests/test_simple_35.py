"""Quick'n'dirty unit tests using async and await syntax."""
import asyncio

import pytest


@pytest.mark.asyncio
async def async_coro(loop):
    await asyncio.sleep(0, loop=loop)
    return 'ok'


@pytest.mark.asyncio
async def test_asyncio_marker():
    """Test the asyncio pytest marker."""


@pytest.mark.asyncio
async def test_asyncio_marker_with_default_param(a_param=None):
    """Test the asyncio pytest marker."""


@pytest.mark.asyncio
async def test_unused_port_fixture(unused_tcp_port, event_loop):
    """Test the unused TCP port fixture."""
    async def closer(_, writer):
        writer.close()

    server1 = await asyncio.start_server(closer, host='localhost',
                                         port=unused_tcp_port,
                                         loop=event_loop)

    server1.close()
    await server1.wait_closed()


def test_unused_port_factory_fixture(unused_tcp_port_factory, event_loop):
    """Test the unused TCP port factory fixture."""

    async def closer(_, writer):
        writer.close()

    port1, port2, port3 = (unused_tcp_port_factory(), unused_tcp_port_factory(),
                           unused_tcp_port_factory())

    async def run_test():
        server1 = await asyncio.start_server(closer, host='localhost',
                                             port=port1,
                                             loop=event_loop)
        server2 = await asyncio.start_server(closer, host='localhost',
                                             port=port2,
                                             loop=event_loop)
        server3 = await asyncio.start_server(closer, host='localhost',
                                             port=port3,
                                             loop=event_loop)

        for port in port1, port2, port3:
            with pytest.raises(IOError):
                await asyncio.start_server(closer, host='localhost',
                                           port=port,
                                           loop=event_loop)

        server1.close()
        await server1.wait_closed()
        server2.close()
        await server2.wait_closed()
        server3.close()
        await server3.wait_closed()

    event_loop.run_until_complete(run_test())

    event_loop.stop()
    event_loop.close()


class Test:
    """Test that asyncio marked functions work in test methods."""

    @pytest.mark.asyncio
    async def test_asyncio_marker_method(self, event_loop):
        """Test the asyncio pytest marker in a Test class."""
        ret = await async_coro(event_loop)
        assert ret == 'ok'


def test_async_close_loop(event_loop):
    event_loop.close()
    return 'ok'


@pytest.mark.asyncio
async def test_advance_time_fixture(event_loop, advance_time):
    """
    Test the `advance_time` fixture using a sleep timer
    """
    # A task is created that will sleep some number of seconds
    SLEEP_TIME = 10

    # create the task
    task = event_loop.create_task(asyncio.sleep(SLEEP_TIME))
    assert not task.done()

    # start the task
    await advance_time(0)
    assert not task.done()

    # process the timeout
    await advance_time(SLEEP_TIME)
    assert task.done()


@pytest.mark.asyncio
async def test_advance_time_fixture_call_later(event_loop, advance_time):
    """
    Test the `advance_time` fixture using loop.call_later
    """
    # A task is created that will sleep some number of seconds
    SLEEP_TIME = 10
    result = []

    # create a simple callback that adds a value to result
    def callback():
        result.append(True)

    # create the task
    event_loop.call_later(SLEEP_TIME, callback)

    # start the task
    await advance_time(0)
    assert not result

    # process the timeout
    await advance_time(SLEEP_TIME)
    assert result


@pytest.mark.asyncio
async def test_advance_time_fixture_coroutine(event_loop, advance_time):
    """
    Test the `advance_time` fixture using loop.call_later
    """
    # A task is created that will sleep some number of seconds
    SLEEP_TIME = 10
    result = []

    # create a simple callback that adds a value to result
    async def callback():
        await asyncio.sleep(SLEEP_TIME)
        result.append(True)

    # create the task
    task = event_loop.create_task(callback())

    # start the task
    await advance_time(0)
    assert not task.done()

    # process the timeout
    await advance_time(SLEEP_TIME)
    assert task.done() and result
