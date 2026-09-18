"""BringupPrompter.suspend drops the TUI around sudo, and degrades to a no-op headless."""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from textual.app import SuspendNotSupported

from wifit3.ui.bringup_prompter import BringupPrompter


def _app(suspend):
    return SimpleNamespace(suspend=suspend)


def test_suspend_releases_and_restores_terminal():
    events = []

    @contextmanager
    def _cm():
        events.append("enter")
        yield
        events.append("exit")

    with BringupPrompter(_app(lambda: _cm())).suspend():
        events.append("body")
    assert events == ["enter", "body", "exit"]


def test_suspend_falls_back_when_unsupported():
    @contextmanager
    def _cm():
        raise SuspendNotSupported("headless driver")
        yield

    ran = []
    with BringupPrompter(_app(lambda: _cm())).suspend():
        ran.append(True)
    assert ran == [True]


def test_suspend_falls_back_without_hook():
    ran = []
    with BringupPrompter(SimpleNamespace()).suspend():
        ran.append(True)
    assert ran == [True]


def test_suspend_propagates_body_errors():
    events = []

    @contextmanager
    def _cm():
        events.append("enter")
        yield
        events.append("exit")

    with pytest.raises(ValueError, match="boom"):
        with BringupPrompter(_app(lambda: _cm())).suspend():
            raise ValueError("boom")
    assert events == ["enter", "exit"]
