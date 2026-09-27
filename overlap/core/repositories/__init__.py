"""
Repository modules for Event Bot.

Provides data access layer abstracting storage implementation.
Repositories handle all database operations for their respective domains.
"""
from overlap.core.repositories.events import EventRepository
from overlap.core.repositories.configs import ConfigRepository
from overlap.core.repositories.users import UserRepository
from overlap.core.repositories.notifications import NotificationRepository
from overlap.core.repositories.availability import AvailabilityMemoryRepository

__all__ = [
    "EventRepository",
    "ConfigRepository",
    "UserRepository",
    "NotificationRepository",
    "AvailabilityMemoryRepository",
]
