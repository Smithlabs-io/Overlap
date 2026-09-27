"""Tests for the plugin loader (overlap/plugins.py)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from overlap import plugins


@pytest.fixture(autouse=True)
def clean_loader(monkeypatch):
    monkeypatch.setattr(plugins, "_loaded", [])


def _entry_point(name, loader):
    return SimpleNamespace(name=name, load=loader)


def _patch_entry_points(monkeypatch, *eps):
    monkeypatch.setattr(plugins, "entry_points", lambda group: list(eps))


def test_no_plugins_is_fine(monkeypatch):
    _patch_entry_points(monkeypatch)
    assert plugins.load_plugins() == []


def test_setup_runs_and_hooks_are_called(monkeypatch):
    plugin = MagicMock()
    plugin.name = "demo"
    _patch_entry_points(monkeypatch, _entry_point("demo", lambda: plugin))

    plugins.load_plugins()
    plugin.setup.assert_called_once()

    tree, guild, app = object(), object(), object()
    plugins.register_commands(tree, guild)
    plugins.register_routes(app)
    plugin.register_commands.assert_called_once_with(tree, guild)
    plugin.register_routes.assert_called_once_with(app)


def test_hooks_are_optional(monkeypatch):
    plugin = SimpleNamespace(name="bare")
    _patch_entry_points(monkeypatch, _entry_point("bare", lambda: plugin))
    plugins.load_plugins()
    plugins.register_commands(object(), object())
    plugins.register_routes(object())


def test_load_is_idempotent(monkeypatch):
    plugin = MagicMock()
    _patch_entry_points(monkeypatch, _entry_point("demo", lambda: plugin))
    plugins.load_plugins()
    plugins.load_plugins()
    plugin.setup.assert_called_once()


def test_broken_plugin_stops_startup(monkeypatch):
    def boom():
        raise ImportError("missing dependency")

    _patch_entry_points(monkeypatch, _entry_point("broken", boom))
    with pytest.raises(ImportError):
        plugins.load_plugins()
