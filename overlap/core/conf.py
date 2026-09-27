"""
Guild configuration — backed by the database (guild_configs table).

All reads/writes go through ConfigRepository; this module is the public API
callers use (`from overlap.core import conf`, `conf.get_config(...)`).
"""
from typing import Any, Dict, Union

from overlap.core.repositories.configs import ConfigRepository, ServerConfigState

__all__ = ["ServerConfigState", "get_config", "modify_config", "delete_config"]


def get_config(guild_id: int) -> ServerConfigState:
    return ConfigRepository.get_config(guild_id)


def modify_config(config: Union[ServerConfigState, Dict[str, Any]]) -> None:
    ConfigRepository.save_config(config)


def delete_config(guild_id: Union[str, int]) -> bool:
    return ConfigRepository.delete_config(guild_id)
