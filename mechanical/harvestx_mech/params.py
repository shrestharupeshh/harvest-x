"""Load design parameters. PyYAML reads ``68.9e9`` as a string; coerce such values."""

from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT = Path(__file__).resolve().parents[1] / "design_params.yaml"


def _coerce(x):
    if isinstance(x, dict):
        return {k: _coerce(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_coerce(v) for v in x]
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return x
    return x


def load_params(path: Path | str = DEFAULT) -> dict:
    return _coerce(yaml.safe_load(Path(path).read_text()))
