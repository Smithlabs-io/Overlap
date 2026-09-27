"""
Plugin hook for optional add-ons.

An add-on is a separate installable package that registers itself under the
`overlap.plugins` entry-point group. Installing it is the opt-in; core never
imports an add-on by name. Example, in the add-on's pyproject.toml:

    [project.entry-points."overlap.plugins"]
    hosted = "my_addon:plugin"

The entry point resolves to an object with a `name` and any of these optional
hooks:

    setup()                          both processes, before anything else
                                     (set an entitlement provider here)
    register_commands(tree, guild)   bot process: add slash commands
    register_routes(app)             web process: add FastAPI routes

A plugin that fails to load stops startup. Falling back to the free edition
silently would drop any gates the add-on was there to enforce.
"""
from importlib.metadata import entry_points
from typing import Any, List

from overlap.core.logging import get_logger

logger = get_logger(__name__)

ENTRY_POINT_GROUP = "overlap.plugins"

_loaded: List[Any] = []


def load_plugins() -> List[Any]:
    """Discover, import and set up every installed plugin. Safe to call twice."""
    if _loaded:
        return list(_loaded)

    for ep in sorted(entry_points(group=ENTRY_POINT_GROUP), key=lambda e: e.name):
        plugin = ep.load()  # any ImportError propagates on purpose
        name = getattr(plugin, "name", ep.name)
        setup = getattr(plugin, "setup", None)
        if setup:
            setup()
        _loaded.append(plugin)
        logger.info(f"Plugin loaded: {name}")

    if not _loaded:
        logger.info("No plugins installed (community edition)")
    return list(_loaded)


def register_commands(tree, guild) -> None:
    for plugin in _loaded:
        hook = getattr(plugin, "register_commands", None)
        if hook:
            hook(tree, guild)


def register_routes(app) -> None:
    for plugin in _loaded:
        hook = getattr(plugin, "register_routes", None)
        if hook:
            hook(app)
