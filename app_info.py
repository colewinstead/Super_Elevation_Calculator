"""Authoritative product and calculation-engine release identifiers."""

APP_NAME = "Superelevation Calculator"
APP_VERSION = "1.4.11"
CALCULATION_ENGINE_VERSION = "1.1.0"


def version_label() -> str:
    return f"{APP_NAME} {APP_VERSION}"
