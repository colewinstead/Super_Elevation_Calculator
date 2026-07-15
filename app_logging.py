"""Per-user rotating logs and user-safe error messages."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback as traceback_module

from app_info import APP_NAME, APP_VERSION


LOGGER_NAME = "superelevation_calculator"
LOG_FILE_NAME = "superelevation.log"
_active_log_path: Path | None = None


def log_directory() -> Path:
    override = os.environ.get("SUPERELEVATION_LOG_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "SuperelevationCalculator" / "Logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "SuperelevationCalculator"
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "superelevation-calculator" / "logs"


def log_path() -> Path:
    return _active_log_path or (log_directory() / LOG_FILE_NAME)


def configure_logging() -> logging.Logger:
    global _active_log_path
    logger = logging.getLogger(LOGGER_NAME)
    if any(getattr(handler, "_superelevation_handler", False) for handler in logger.handlers):
        return logger
    directory = log_directory()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        directory = Path(tempfile.gettempdir()) / "SuperelevationCalculator" / "Logs"
        directory.mkdir(parents=True, exist_ok=True)
    _active_log_path = directory / LOG_FILE_NAME
    handler = RotatingFileHandler(_active_log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler._superelevation_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info("Application logging initialized app_version=%s", APP_VERSION)
    return logger


def record_exception(operation: str, exc: BaseException) -> Path:
    logger = configure_logging()
    logger.error(
        "operation_failed operation=%s exception_type=%s message=%s",
        operation,
        type(exc).__name__,
        str(exc),
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return log_path()


def record_uncaught_exception(exc_type: type[BaseException], exc: BaseException, tb: object) -> Path:
    logger = configure_logging()
    logger.critical(
        "uncaught_exception exception_type=%s message=%s\n%s",
        exc_type.__name__,
        str(exc),
        "".join(traceback_module.format_exception(exc_type, exc, tb)),
    )
    return log_path()


def open_log_directory() -> None:
    directory = log_path().parent
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(directory)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(directory)], check=True)
    else:
        subprocess.run(["xdg-open", str(directory)], check=True)


def friendly_error(operation: str, exc: BaseException, path: str | os.PathLike[str] | None = None) -> str:
    name = Path(path).name if path else "the selected file"
    if isinstance(exc, FileNotFoundError):
        return f"{name} could not be found. It may have been moved, renamed, or deleted."
    if isinstance(exc, PermissionError):
        return f"Permission was denied for {name}. Close other programs using it or choose a writable location."
    if isinstance(exc, IsADirectoryError):
        return f"{name} is a folder, not a file. Select a file and try again."
    if operation == "landxml":
        from xml.etree.ElementTree import ParseError

        if isinstance(exc, ParseError):
            return f"{name} is not well-formed XML. Re-export the LandXML and try again."
        if isinstance(exc, ValueError):
            return f"{name} could not be used as LandXML: {exc}"
        return f"The LandXML file {name} could not be read."
    if operation == "project_load":
        return f"The project {name} could not be opened: {exc}"
    if operation == "project_save":
        return f"The project could not be saved to {name}."
    if operation == "pdf_export":
        return f"The PDF report could not be created at {name}."
    if operation == "csv_export":
        return f"The ORD CSV could not be created at {name}."
    if operation in {"detail_dxf_export", "overlay_dxf_export"}:
        return f"The DXF could not be created at {name}."
    return f"{APP_NAME} could not complete {operation.replace('_', ' ')}."
