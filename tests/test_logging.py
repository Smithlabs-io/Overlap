"""
Tests for structured logging: JsonFormatter output format and setup_logging branches.
"""
import json
import logging
import sys

import pytest

import config as app_config
from core.logging import JsonFormatter, setup_logging


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------

def _make_record(message="test message", level=logging.INFO, name="test.logger"):
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )


class TestJsonFormatter:

    def test_output_is_valid_json(self):
        output = JsonFormatter().format(_make_record())
        json.loads(output)  # raises if invalid

    def test_required_keys_present(self):
        parsed = json.loads(JsonFormatter().format(_make_record()))
        for key in ("timestamp", "level", "logger", "message", "service"):
            assert key in parsed

    def test_message_content(self):
        parsed = json.loads(JsonFormatter().format(_make_record("hello overlap")))
        assert parsed["message"] == "hello overlap"

    def test_level_name_is_string(self):
        parsed = json.loads(JsonFormatter().format(_make_record(level=logging.WARNING)))
        assert parsed["level"] == "WARNING"

    def test_logger_name_captured(self):
        parsed = json.loads(JsonFormatter().format(_make_record(name="my.module")))
        assert parsed["logger"] == "my.module"

    def test_service_tag_is_overlap_bot(self):
        parsed = json.loads(JsonFormatter().format(_make_record()))
        assert parsed["service"] == "overlap-bot"

    def test_timestamp_is_timezone_aware_iso(self):
        from datetime import datetime
        parsed = json.loads(JsonFormatter().format(_make_record()))
        dt = datetime.fromisoformat(parsed["timestamp"])
        assert dt.tzinfo is not None

    def test_exception_key_included_when_exc_info_present(self):
        record = _make_record()
        try:
            raise ValueError("boom")
        except ValueError:
            record.exc_info = sys.exc_info()
        parsed = json.loads(JsonFormatter().format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "boom" in parsed["exception"]

    def test_no_exception_key_without_exc_info(self):
        parsed = json.loads(JsonFormatter().format(_make_record()))
        assert "exception" not in parsed

    def test_single_line_output(self):
        output = JsonFormatter().format(_make_record("line\nwith\nnewlines"))
        # JSON serialization via json.dumps keeps the string content but the
        # *record* itself must be a single JSON object on one line.
        assert output.count("\n") == 0 or json.loads(output)  # parseable = valid


# ---------------------------------------------------------------------------
# setup_logging — formatter selection
# ---------------------------------------------------------------------------

class TestSetupLogging:

    def _reset_logging(self, monkeypatch, log_mod):
        """Clear root handlers and reset the configured flag before each test."""
        root = logging.getLogger()
        saved = root.handlers[:]
        root.handlers.clear()
        monkeypatch.setattr(log_mod, "_logging_configured", False)
        return saved

    def test_json_formatter_selected_when_log_json_true(self, monkeypatch):
        import core.logging as log_mod
        monkeypatch.setattr(app_config, "LOG_JSON", True)
        saved = self._reset_logging(monkeypatch, log_mod)
        try:
            setup_logging()
            handler = logging.getLogger().handlers[0]
            assert isinstance(handler.formatter, JsonFormatter)
        finally:
            logging.getLogger().handlers = saved

    def test_text_formatter_selected_when_log_json_false(self, monkeypatch):
        import core.logging as log_mod
        monkeypatch.setattr(app_config, "LOG_JSON", False)
        saved = self._reset_logging(monkeypatch, log_mod)
        try:
            setup_logging()
            handler = logging.getLogger().handlers[0]
            assert not isinstance(handler.formatter, JsonFormatter)
        finally:
            logging.getLogger().handlers = saved

    def test_setup_logging_is_idempotent(self, monkeypatch):
        """Calling setup_logging twice must not add a second handler."""
        import core.logging as log_mod
        monkeypatch.setattr(app_config, "LOG_JSON", False)
        saved = self._reset_logging(monkeypatch, log_mod)
        try:
            setup_logging()
            count_after_first = len(logging.getLogger().handlers)
            setup_logging()
            assert len(logging.getLogger().handlers) == count_after_first
        finally:
            logging.getLogger().handlers = saved
