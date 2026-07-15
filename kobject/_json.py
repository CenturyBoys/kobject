"""JSON backend that prefers orjson when installed, falling back to stdlib json.

orjson (an optional dependency) is used automatically when importable, giving
faster encode/decode. The stdlib ``json`` module is used otherwise. Both paths
produce the same compact output for ASCII payloads; orjson emits raw UTF-8 for
non-ASCII strings where stdlib emits ``\\uXXXX`` escapes.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

try:
    import orjson

    _HAS_ORJSON = True
except ImportError:  # pragma: no cover - exercised only without the optional extra
    _HAS_ORJSON = False


def dumps(obj: Any, default: Callable[[Any], Any]) -> bytes:
    """Serialize ``obj`` to compact JSON bytes."""
    if _HAS_ORJSON:
        # OPT_PASSTHROUGH_DATETIME routes datetime/date/time through ``default`` so
        # behavior matches the stdlib backend, which relies on encoder resolvers.
        return orjson.dumps(
            obj, default=default, option=orjson.OPT_PASSTHROUGH_DATETIME
        )
    return json.dumps(obj, default=default, separators=(",", ":")).encode()


def loads(payload: bytes) -> Any:
    """Deserialize JSON ``payload`` to Python objects."""
    if _HAS_ORJSON:
        return orjson.loads(payload)
    return json.loads(payload)
