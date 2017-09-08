"""Quick'n'dirty unit tests for provided fixtures and markers."""
import asyncio
import os
import pytest

import pytest_asyncio.plugin


@asyncio.coroutine
def async_coro(loop=None):
    """A very simple coroutine."""
    yield from asyncio.sleep(0, loop=loop)
    return 'ok'


def test_event_loop_fixture(event_loop):
    """Test the injection of the event_loop fixture."""
    assert event_loop
    ret = event_loop.run_until_complete(async_coro(event_loop))
    assert ret == 'ok'


def test_event_loop_processpool_fixture(event_loop_process_pool):
    """Test the injection of the event_loop with a process pool fixture."""
    assert event_loop_process_pool

    ret = event_loop_process_pool.run_until_complete(
        async_coro(event_loop_process_pool))
    assert ret == 'ok'

    this_pid = os.getpid()
    future = event_loop_process_pool.run_in_executor(None, os.getpid)
    pool_pid = event_loop_process_pool.run_until_complete(future)
    assert this_pid != pool_pid


@pytest.mark.asyncio
def test_asyncio_marker():
    """Test the asyncio pytest marker."""
    yield  # sleep(0)


@pytest.mark.xfail(reason='need a failure', strict=True)
@pytest.mark.asyncio
def test_asyncio_marker_fail():
    assert False


@pytest.mark.asyncio
def test_asyncio_marker_with_default_param(a_param=None):
    """Test the asyncio pytest marker."""
    yield  # sleep(0)


@pytest.mark.asyncio_process_pool
def test_asyncio_process_pool_marker(event_loop):
    """Test the asyncio pytest marker."""
    ret = yield from async_coro(event_loop)
    assert ret == 'ok'


@pytest.mark.asyncio
def test_unused_port_fixture(unused_tcp_port, event_loop):
    """Test the unused TCP port fixture."""

    @asyncio.coroutine
    def closer(_, writer):
        writer.close()

    server1 = yield from asyncio.start_server(closer, host='localhost',
                                              port=unused_tcp_port,
                                              loop=event_loop)

    with pytest.raises(IOError):
        yield from asyncio.start_server(closer, host='localhost',
                                        port=unused_tcp_port,
                                        loop=event_loop)

    server1.close()
    yield from server1.wait_closed()


@pytest.mark.asyncio
def test_unused_port_factory_fixture(unused_tcp_port_factory, event_loop):
    """Test the unused TCP port factory fixture."""

    @asyncio.coroutine
    def closer(_, writer):
        writer.close()

    port1, port2, port3 = (unused_tcp_port_factory(), unused_tcp_port_factory(),
                           unused_tcp_port_factory())

    server1 = yield from asyncio.start_server(closer, host='localhost',
                                              port=port1,
                                              loop=event_loop)
    server2 = yield from asyncio.start_server(closer, host='localhost',
                                              port=port2,
                                              loop=event_loop)
    server3 = yield from asyncio.start_server(closer, host='localhost',
                                              port=port3,
                                              loop=event_loop)

    for port in port1, port2, port3:
        with pytest.raises(IOError):
            yield from asyncio.start_server(closer, host='localhost',
                                            port=port,
                                            loop=event_loop)

    server1.close()
    yield from server1.wait_closed()
    server2.close()
    yield from server2.wait_closed()
    server3.close()
    yield from server3.wait_closed()


def test_unused_port_factory_duplicate(unused_tcp_port_factory, monkeypatch):
    """Test correct avoidance of duplicate ports."""
    counter = 0

    def mock_unused_tcp_port():
        """Force some duplicate ports."""
        nonlocal counter
        counter += 1
        if counter < 5:
            return 10000
        else:
            return 10000 + counter

    monkeypatch.setattr(pytest_asyncio.plugin, 'unused_tcp_port',
                        mock_unused_tcp_port)

    assert unused_tcp_port_factory() == 10000
    assert unused_tcp_port_factory() > 10000


class Test:
    """Test that asyncio marked functions work in test methods."""

    @pytest.mark.asyncio
    def test_asyncio_marker_method(self, event_loop):
        """Test the asyncio pytest marker in a Test class."""
        ret = yield from async_coro(event_loop)
        assert ret == 'ok'


class TestUnexistingLoop:

    @pytest.fixture
    def remove_loop(self):
        old_loop = asyncio.get_event_loop()
        asyncio.set_event_loop(None)
        yield
        asyncio.set_event_loop(old_loop)

    @pytest.mark.asyncio
    def test_asyncio_marker_without_loop(self, remove_loop):
        """Test the asyncio pytest marker in a Test class."""
        ret = yield from async_coro()
        assert ret == 'ok'
