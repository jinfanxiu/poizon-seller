"""app.py 비밀번호 화면: on_change session_state KeyError 회귀 방지."""

from __future__ import annotations

import os

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def password_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PASSWORD", "test-secret-ok")
    monkeypatch.setenv("GH_TOKEN", "")


def test_password_screen_runs_without_keyerror(password_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    at = AppTest.from_file("app.py")
    at.run(timeout=60)
    assert not list(at.exception), list(at.exception)
    assert len(at.text_input) == 1

    at.text_input[0].set_value("wrong-password").run()
    assert not list(at.exception), list(at.exception)
    at.button[0].click().run()
    assert not list(at.exception), list(at.exception)
    assert len(at.error) >= 1

    at.text_input[0].set_value("test-secret-ok").run()
    at.button[0].click().run()
    assert not list(at.exception), list(at.exception)
    assert len(at.title) >= 1
