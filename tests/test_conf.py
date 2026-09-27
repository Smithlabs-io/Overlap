"""
Tests for core/conf.py (delegates to ConfigRepository, OVERLAP-7).

modify_config's SQL used to live in two places: conf.py (complete, the one
actually called) and ConfigRepository (unused, missing the use_24hr_time and
bulletin_use_threads columns). Consolidating onto ConfigRepository would have
silently dropped those two settings on every save if the columns hadn't been
added back — this locks that in.
"""
from overlap.core import conf
from overlap.core.conf import ServerConfigState

GUILD_ID = 424242


def test_modify_config_round_trips_all_columns():
    conf.modify_config(ServerConfigState(
        guild_id=str(GUILD_ID),
        use_24hr_time=True,
        bulletin_use_threads=False,
        default_reminder_minutes=15,
    ))
    fetched = conf.get_config(GUILD_ID)
    assert fetched.use_24hr_time is True
    assert fetched.bulletin_use_threads is False
    assert fetched.default_reminder_minutes == 15


def test_get_config_creates_default_on_first_access():
    fetched = conf.get_config(GUILD_ID)
    assert fetched.guild_id == str(GUILD_ID)
    assert fetched.use_24hr_time is False  # dataclass default


def test_modify_config_is_an_upsert():
    conf.modify_config(ServerConfigState(guild_id=str(GUILD_ID), default_reminder_minutes=30))
    conf.modify_config(ServerConfigState(guild_id=str(GUILD_ID), default_reminder_minutes=45))
    assert conf.get_config(GUILD_ID).default_reminder_minutes == 45


def test_delete_config():
    conf.modify_config(ServerConfigState(guild_id=str(GUILD_ID)))
    assert conf.delete_config(GUILD_ID) is True
    assert conf.delete_config(GUILD_ID) is False
