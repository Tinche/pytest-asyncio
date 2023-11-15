from textwrap import dedent

from pytest import Pytester


def test_asyncio_mark_provides_session_scoped_loop_strict_mode(pytester: Pytester):
    package_name = pytester.path.name
    pytester.makepyfile(
        __init__="",
        shared_module=dedent(
            """\
            import asyncio

            loop: asyncio.AbstractEventLoop = None
            """
        ),
        test_module_one=dedent(
            f"""\
            import asyncio
            import pytest

            from {package_name} import shared_module

            @pytest.mark.asyncio(scope="session")
            async def test_remember_loop():
                shared_module.loop = asyncio.get_running_loop()
            """
        ),
        test_module_two=dedent(
            f"""\
            import asyncio
            import pytest

            from {package_name} import shared_module

            pytestmark = pytest.mark.asyncio(scope="session")

            async def test_this_runs_in_same_loop():
                assert asyncio.get_running_loop() is shared_module.loop

            class TestClassA:
                async def test_this_runs_in_same_loop(self):
                    assert asyncio.get_running_loop() is shared_module.loop
            """
        ),
    )
    subpackage_name = "subpkg"
    subpkg = pytester.mkpydir(subpackage_name)
    subpkg.joinpath("test_subpkg.py").write_text(
        dedent(
            f"""\
            import asyncio
            import pytest

            from {package_name} import shared_module

            pytestmark = pytest.mark.asyncio(scope="session")

            async def test_subpackage_runs_in_same_loop():
                assert asyncio.get_running_loop() is shared_module.loop
            """
        )
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(passed=4)


def test_raise_when_event_loop_fixture_is_requested_in_addition_to_scoped_loop(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        test_raises=dedent(
            """\
            import asyncio
            import pytest

            @pytest.mark.asyncio(scope="session")
            async def test_remember_loop(event_loop):
                pass
            """
        ),
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines("*MultipleEventLoopsRequestedError: *")


def test_asyncio_mark_respects_the_loop_policy(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        conftest=dedent(
            """\
            import pytest

            from .custom_policy import CustomEventLoopPolicy

            @pytest.fixture(scope="session")
            def event_loop_policy():
                return CustomEventLoopPolicy()
            """
        ),
        custom_policy=dedent(
            """\
            import asyncio

            class CustomEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
                pass
            """
        ),
        test_uses_custom_policy=dedent(
            """\
            import asyncio
            import pytest

            from .custom_policy import CustomEventLoopPolicy

            pytestmark = pytest.mark.asyncio(scope="session")

            async def test_uses_custom_event_loop_policy():
                assert isinstance(
                    asyncio.get_event_loop_policy(),
                    CustomEventLoopPolicy,
                )
            """
        ),
        test_also_uses_custom_policy=dedent(
            """\
            import asyncio
            import pytest

            from .custom_policy import CustomEventLoopPolicy

            pytestmark = pytest.mark.asyncio(scope="session")

            async def test_also_uses_custom_event_loop_policy():
                assert isinstance(
                    asyncio.get_event_loop_policy(),
                    CustomEventLoopPolicy,
                )
            """
        ),
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(passed=2)


def test_asyncio_mark_respects_parametrized_loop_policies(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        test_parametrization=dedent(
            """\
            import asyncio

            import pytest

            pytestmark = pytest.mark.asyncio(scope="session")

            @pytest.fixture(
                scope="session",
                params=[
                    asyncio.DefaultEventLoopPolicy(),
                    asyncio.DefaultEventLoopPolicy(),
                ],
            )
            def event_loop_policy(request):
                return request.param

            async def test_parametrized_loop():
                pass
            """
        ),
    )
    result = pytester.runpytest_subprocess("--asyncio-mode=strict")
    result.assert_outcomes(passed=2)


def test_asyncio_mark_provides_session_scoped_loop_to_fixtures(
    pytester: Pytester,
):
    package_name = pytester.path.name
    pytester.makepyfile(
        __init__="",
        conftest=dedent(
            f"""\
            import asyncio

            import pytest_asyncio

            from {package_name} import shared_module

            @pytest_asyncio.fixture(scope="session")
            async def my_fixture():
                shared_module.loop = asyncio.get_running_loop()
            """
        ),
        shared_module=dedent(
            """\
            import asyncio

            loop: asyncio.AbstractEventLoop = None
            """
        ),
    )
    subpackage_name = "subpkg"
    subpkg = pytester.mkpydir(subpackage_name)
    subpkg.joinpath("test_subpkg.py").write_text(
        dedent(
            f"""\
            import asyncio

            import pytest
            import pytest_asyncio

            from {package_name} import shared_module

            pytestmark = pytest.mark.asyncio(scope="session")

            async def test_runs_in_same_loop_as_fixture(my_fixture):
                assert asyncio.get_running_loop() is shared_module.loop
            """
        )
    )
    result = pytester.runpytest_subprocess("--asyncio-mode=strict")
    result.assert_outcomes(passed=1)


def test_asyncio_mark_allows_combining_session_scoped_fixture_with_package_scoped_test(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        test_mixed_scopes=dedent(
            """\
            import asyncio

            import pytest
            import pytest_asyncio

            loop: asyncio.AbstractEventLoop

            @pytest_asyncio.fixture(scope="session")
            async def async_fixture():
                global loop
                loop = asyncio.get_running_loop()

            @pytest.mark.asyncio(scope="package")
            async def test_runs_in_different_loop_as_fixture(async_fixture):
                global loop
                assert asyncio.get_running_loop() is not loop
            """
        ),
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(passed=1)


def test_asyncio_mark_allows_combining_session_scoped_fixture_with_module_scoped_test(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        test_mixed_scopes=dedent(
            """\
            import asyncio

            import pytest
            import pytest_asyncio

            loop: asyncio.AbstractEventLoop

            @pytest_asyncio.fixture(scope="session")
            async def async_fixture():
                global loop
                loop = asyncio.get_running_loop()

            @pytest.mark.asyncio(scope="module")
            async def test_runs_in_different_loop_as_fixture(async_fixture):
                global loop
                assert asyncio.get_running_loop() is not loop
            """
        ),
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(passed=1)


def test_asyncio_mark_allows_combining_session_scoped_fixture_with_class_scoped_test(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        test_mixed_scopes=dedent(
            """\
            import asyncio

            import pytest
            import pytest_asyncio

            loop: asyncio.AbstractEventLoop

            @pytest_asyncio.fixture(scope="session")
            async def async_fixture():
                global loop
                loop = asyncio.get_running_loop()

            @pytest.mark.asyncio(scope="class")
            class TestMixedScopes:
                async def test_runs_in_different_loop_as_fixture(self, async_fixture):
                    global loop
                    assert asyncio.get_running_loop() is not loop
            """
        ),
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(passed=1)


def test_asyncio_mark_allows_combining_session_scoped_fixture_with_function_scoped_test(
    pytester: Pytester,
):
    pytester.makepyfile(
        __init__="",
        test_mixed_scopes=dedent(
            """\
            import asyncio

            import pytest
            import pytest_asyncio

            loop: asyncio.AbstractEventLoop

            @pytest_asyncio.fixture(scope="session")
            async def async_fixture():
                global loop
                loop = asyncio.get_running_loop()

            @pytest.mark.asyncio
            async def test_runs_in_different_loop_as_fixture(async_fixture):
                global loop
                assert asyncio.get_running_loop() is not loop
            """
        ),
    )
    result = pytester.runpytest("--asyncio-mode=strict")
    result.assert_outcomes(passed=1)
