"""Authoritative product and calculation-engine release identifiers."""

APP_NAME = "Superelevation Calculator"
APP_VERSION = "1.2.1"
CALCULATION_ENGINE_VERSION = "1.0.0"


def version_label() -> str:
    return f"{APP_NAME} {APP_VERSION}"
