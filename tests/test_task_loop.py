"""The scheduled-task loop.

Two faults lived here. A blank schedule entry meant "use the fallback interval"
rather than "disabled", and only library_sync had a fallback, so blanking its
entry ran it every thirty minutes instead of stopping it. And the error branch
retried with no delay, so an unsatisfiable cron spun the loop as fast as the CPU
allowed — about 40,000 tracebacks in two minutes, starving the event loop
(ath-m4i).
"""
import asyncio

import pytest

from app import main as app_main

# Captured before any test patches asyncio.sleep. The harness yields with this so
# its own yields are not recorded as sleeps by the tests measuring them — which is
# exactly what made the backoff assertion see a list of alternating 0s and 60s.
_REAL_SLEEP = asyncio.sleep


async def _run_briefly(coro_fn, *args, **kwargs):
    """Start the loop, let it settle, then cancel it."""
    task = asyncio.create_task(coro_fn(*args, **kwargs))
    for _ in range(50):          # yield repeatedly so the loop can progress
        await _REAL_SLEEP(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.fixture
def no_waiting(monkeypatch):
    """Make every sleep and cron wait instant, and count them by duration."""
    slept: list[float] = []
    async def fake_sleep(d):
        slept.append(d)
        await _REAL_SLEEP(0)

    async def instant_cron(expr):
        slept.append(("cron", expr))
        await _REAL_SLEEP(0)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(app_main, "_wait_until_next", instant_cron)
    return slept


def _settings_with(schedule: dict):
    async def get(*a, **kw):
        return {"schedule": schedule}
    return get


class TestBlankMeansDisabled:
    @pytest.mark.asyncio
    async def test_a_blank_entry_never_runs_the_task(self, monkeypatch, no_waiting):
        """The regression: this used to run every fallback_interval instead."""
        monkeypatch.setattr(app_main, "get_settings", _settings_with({"library_sync": ""}))
        ran = []

        async def task():
            ran.append(1)

        await _run_briefly(
            app_main._task_loop, "library_sync_task", "library_sync", task,
            fallback_interval=1800,
        )
        assert ran == [], "a blank schedule entry still ran the task"

    @pytest.mark.asyncio
    async def test_whitespace_counts_as_blank(self, monkeypatch, no_waiting):
        monkeypatch.setattr(app_main, "get_settings", _settings_with({"library_sync": "   "}))
        ran = []

        async def task():
            ran.append(1)

        await _run_briefly(
            app_main._task_loop, "library_sync_task", "library_sync", task,
            fallback_interval=1800,
        )
        assert ran == []

    @pytest.mark.asyncio
    async def test_an_absent_key_still_uses_the_fallback(self, monkeypatch, no_waiting):
        """A fresh install that has never had a schedule written must still run."""
        monkeypatch.setattr(app_main, "get_settings", _settings_with({}))
        ran = []

        async def task():
            ran.append(1)

        await _run_briefly(
            app_main._task_loop, "library_sync_task", "library_sync", task,
            fallback_interval=1800,
        )
        assert ran, "an unconfigured task with a fallback should still run"
        assert 1800 in no_waiting

    @pytest.mark.asyncio
    async def test_a_real_cron_runs_the_task(self, monkeypatch, no_waiting):
        monkeypatch.setattr(app_main, "get_settings", _settings_with({"cache_refresh": "0 3 * * *"}))
        ran = []

        async def task():
            ran.append(1)

        await _run_briefly(app_main._task_loop, "cache_refresh_task", "cache_refresh", task)
        assert ran
        assert ("cron", "0 3 * * *") in no_waiting


class TestErrorsBackOff:
    @pytest.mark.asyncio
    async def test_a_failing_task_waits_before_retrying(self, monkeypatch, no_waiting):
        """Without a backoff an error that recurs every pass is a busy loop — which
        is what an impossible cron date did, croniter raising on every iteration."""
        monkeypatch.setattr(app_main, "get_settings", _settings_with({"cache_refresh": "0 3 * * *"}))
        attempts = []

        async def boom():
            attempts.append(1)
            raise RuntimeError("always fails")

        await _run_briefly(app_main._task_loop, "cache_refresh_task", "cache_refresh", boom)
        assert attempts, "the task should have been attempted"
        assert app_main._TASK_ERROR_BACKOFF in no_waiting, (
            f"no backoff after failure; slept {no_waiting}"
        )

    @pytest.mark.asyncio
    async def test_an_unsatisfiable_cron_does_not_spin(self, monkeypatch):
        """30 February never occurs, so croniter raises every pass. The loop must
        pace itself rather than retry instantly."""
        monkeypatch.setattr(
            app_main, "get_settings", _settings_with({"cache_refresh": "0 0 30 2 *"})
        )
        slept: list[float] = []

        async def fake_sleep(d):
            slept.append(d)
            await _REAL_SLEEP(0)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        async def task():
            pass

        await _run_briefly(app_main._task_loop, "cache_refresh_task", "cache_refresh", task)
        assert slept, "the loop retried with no delay at all"
        assert all(d >= app_main._TASK_ERROR_BACKOFF for d in slept), slept
