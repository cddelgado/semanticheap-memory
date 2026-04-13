"""Temporal parsing and scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re

from .exceptions import InvalidTemporalExpressionError


_TEMPORAL_PATTERN = re.compile(r"^([+-])(\d+)([hdwmy])$")


@dataclass(slots=True)
class TemporalBias:
    """Parsed temporal bias metadata."""

    expression: str
    target_seconds: float
    direction: int


def parse_temporal_expression(expression: str) -> TemporalBias:
    """Parse a temporal relevance expression into a normalized bias object."""
    expr = expression.strip().lower()
    if expr == "now":
        return TemporalBias(expression="now", target_seconds=0.0, direction=0)

    match = _TEMPORAL_PATTERN.match(expr)
    if not match:
        raise InvalidTemporalExpressionError(f"Unsupported temporal relevance: {expression}")

    sign, amount_raw, unit = match.groups()
    amount = int(amount_raw)
    unit_seconds = {
        "h": 3600,
        "d": 86400,
        "w": 7 * 86400,
        "m": 30 * 86400,
        "y": 365 * 86400,
    }[unit]
    seconds = amount * unit_seconds
    direction = 1 if sign == "+" else -1
    return TemporalBias(expression=expr, target_seconds=direction * seconds, direction=direction)


def temporal_fit_score(temporal_bias: TemporalBias, created_at: datetime, now: datetime | None = None) -> float:
    """Score fit of an idea timestamp against requested temporal relevance."""
    current = now or datetime.now(UTC)
    delta_seconds = (created_at - current).total_seconds()

    if temporal_bias.expression == "now":
        # Exponential-like drop-off in a simple explainable form.
        return max(0.0, 1.0 - min(abs(delta_seconds) / (14 * 86400), 1.0))

    target = temporal_bias.target_seconds
    max_range = max(abs(target), 86400)
    distance = abs(delta_seconds - target)
    return max(0.0, 1.0 - min(distance / (3 * max_range), 1.0))


def decay_strength(base_strength: float, decay_rate: float, created_at: datetime, now: datetime | None = None) -> float:
    """Apply simple age-based linear decay to strength."""
    current = now or datetime.now(UTC)
    age_days = max(0.0, (current - created_at).total_seconds() / 86400)
    adjusted = base_strength - decay_rate * age_days
    return max(0.0, adjusted)


def parse_datetime(value: str) -> datetime:
    """Parse an ISO datetime stored in SQLite."""
    return datetime.fromisoformat(value)


def now_iso() -> str:
    """Return an ISO UTC timestamp."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def offset_now(**kwargs: int) -> str:
    """Helper for tests and fixtures to produce offset timestamps."""
    return (datetime.now(UTC) + timedelta(**kwargs)).replace(microsecond=0).isoformat()
