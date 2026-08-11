import logging
import logging.handlers
from pathlib import Path

from logging_utils.logger import get_logger


def test_get_logger_returns_same_instance_no_duplicate_handlers():
    logger_a = get_logger("test.logging_utils.same_instance")
    handler_count_after_first_call = len(logger_a.handlers)

    logger_b = get_logger("test.logging_utils.same_instance")

    assert logger_a is logger_b
    assert len(logger_b.handlers) == handler_count_after_first_call


def test_get_logger_has_console_and_file_handlers_by_default():
    logger = get_logger("test.logging_utils.console_and_file")

    console_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    file_handlers = [
        h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
    ]
    assert len(console_handlers) == 1
    assert len(file_handlers) == 1


def test_get_logger_falls_back_when_log_dir_uncreatable(monkeypatch, caplog):
    def raise_oserror(self, *args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "mkdir", raise_oserror)

    with caplog.at_level(logging.WARNING):
        logger = get_logger("test.logging_utils.uncreatable_dir")

    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    assert not any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers
    )
    assert "File logging unavailable" in caplog.text
