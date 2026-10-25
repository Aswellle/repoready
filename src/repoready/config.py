"""TOML configuration loading (docs/spec/01-architecture-rules.md §6).

Frozen schema:

    [rules]
    disable = ["<rule_id>", ...]

    [ignore]
    paths = ["<relative path or glob>", ...]

Unknown keys, wrong types, unregistered rule ids, and ignore paths
that are absolute or escape the repository root are configuration
errors; the CLI maps ConfigError to exit code 2. No executable
expressions, no plugin imports. Thresholds and output-format keys do
not exist (no scores; output format is a CLI flag).
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .rules.registry import get_spec

DRIVE_RE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True)
class Config:
    disabled_rules: frozenset[str] = frozenset()
    ignore_paths: tuple[str, ...] = ()


DEFAULT_CONFIG = Config()


class ConfigError(Exception):
    """Raised for invalid configuration; CLI maps this to exit code 2."""


def load_config(path: str | Path) -> Config:
    config_path = Path(path)
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(
            f"cannot read config '{config_path}': {exc.strerror or exc}"
        ) from exc
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        summary = str(exc).splitlines()[0][:200]
        raise ConfigError(
            f"config '{config_path}' is not valid TOML: {summary}"
        ) from exc
    unknown = sorted(set(data) - {"rules", "ignore"})
    if unknown:
        raise ConfigError(
            f"config '{config_path}': unknown key(s) {unknown}; "
            "allowed top-level keys: rules, ignore"
        )
    disabled = _load_disabled(data.get("rules"), config_path)
    ignore_paths = _load_ignore(data.get("ignore"), config_path)
    return Config(frozenset(disabled), tuple(ignore_paths))


def _load_disabled(value, config_path: Path) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        raise ConfigError(
            f"config '{config_path}': 'rules' must be a table"
        )
    unknown = sorted(set(value) - {"disable"})
    if unknown:
        raise ConfigError(
            f"config '{config_path}': unknown key(s) in [rules]: {unknown}; "
            "allowed: disable"
        )
    disable = value["disable"]
    if disable is None:
        return []
    if not isinstance(disable, list) or any(
        not isinstance(entry, str) for entry in disable
    ):
        raise ConfigError(
            f"config '{config_path}': 'rules.disable' must be an array "
            "of rule_id strings"
        )
    for rule_id in disable:
        try:
            get_spec(rule_id)
        except LookupError:
            raise ConfigError(
                f"config '{config_path}': 'rules.disable' contains "
                f"unregistered rule_id '{rule_id}'"
            ) from None
    return disable


def _load_ignore(value, config_path: Path) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        raise ConfigError(
            f"config '{config_path}': 'ignore' must be a table"
        )
    unknown = sorted(set(value) - {"paths"})
    if unknown:
        raise ConfigError(
            f"config '{config_path}': unknown key(s) in [ignore]: {unknown}; "
            "allowed: paths"
        )
    paths = value["paths"]
    if paths is None:
        return []
    if not isinstance(paths, list) or any(
        not isinstance(entry, str) for entry in paths
    ):
        raise ConfigError(
            f"config '{config_path}': 'ignore.paths' must be an array "
            "of relative path strings"
        )
    return [_validate_ignore_path(entry, config_path) for entry in paths]


def _validate_ignore_path(raw: str, config_path: Path) -> str:
    normalized = raw.replace("\\", "/").strip()
    if not normalized:
        raise ConfigError(
            f"config '{config_path}': 'ignore.paths' contains an empty path"
        )
    if PurePosixPath(normalized).is_absolute() or DRIVE_RE.match(normalized):
        raise ConfigError(
            f"config '{config_path}': ignore path '{raw}' is absolute; "
            "paths must be relative to the repository root"
        )
    if ".." in PurePosixPath(normalized).parts:
        raise ConfigError(
            f"config '{config_path}': ignore path '{raw}' contains '..'; "
            "paths must stay inside the repository root"
        )
    return normalized
