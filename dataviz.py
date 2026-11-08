"""Small, dependency-free data shaping for the debrief charts.

The simulator keeps its flight results in memory. This module turns those
records into a consistent set of bars and target marks without importing Tk,
so the data rules can be tested on a headless machine.
"""

from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(frozen=True)
class Metric:
    """One row in a bar chart. ``fraction`` is always clamped to 0..1."""

    label: str
    value: float
    limit: float
    display: str
    target: Optional[float] = None
    better: str = "higher"
    tone: str = "default"

    @property
    def fraction(self):
        if self.limit <= 0:
            return 0.0
        return _clamp(self.value / self.limit, 0.0, 1.0)

    @property
    def target_fraction(self):
        if self.target is None or self.limit <= 0:
            return None
        return _clamp(self.target / self.limit, 0.0, 1.0)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _number(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return number


def _rows(rows):
    return tuple(metric for metric in rows if metric is not None)


def telemetry_metrics(stats=None, success=True):
    """Map a flight record to the two or three bars shown in the debrief."""
    if not isinstance(stats, Mapping):
        return ()
    mode = stats.get("mode")

    if mode == "load":
        stability = _clamp(_number(stats.get("stability")), 0.0, 100.0)
        load = _clamp(_number(stats.get("load")), 0.0, 100.0)
        return _rows((
            Metric("STABILITY", stability, 100.0, "{0:.0f}%".format(stability)),
            Metric("LOAD", load, 100.0, "{0:.0f}%".format(load)),
        ))

    if mode == "landing":
        speed = max(0.0, _number(stats.get("speed")))
        miss = max(0.0, _number(stats.get("miss")))
        fuel = _clamp(_number(stats.get("fuel")), 0.0, 100.0)
        target_half = _clamp(_number(stats.get("target_half"), 30.0), 1.0, 100.0)
        miss_limit = target_half + 16.0
        return _rows((
            Metric(
                "TOUCHDOWN SPEED" if success else "IMPACT SPEED",
                speed, 20.0, "{0:.1f} M/S".format(speed),
                target=9.5, better="lower",
                tone="default" if speed <= 9.5 else "bad",
            ),
            Metric(
                "MISS DISTANCE", miss, miss_limit, "{0:.1f} M".format(miss),
                target=target_half, better="lower",
                tone="default" if miss <= target_half else ("warn" if miss <= miss_limit else "bad"),
            ),
            Metric(
                "FUEL REMAINING", fuel, 100.0, "{0:.0f}%".format(fuel),
                target=30.0,
                tone="default" if fuel >= 30.0 else "bad",
            ),
        ))

    if mode == "debris":
        max_hull = int(_clamp(_number(stats.get("max_hull"), 4), 1, 8))
        hull = _clamp(_number(stats.get("hull")), 0.0, float(max_hull))
        close = max(0.0, _number(stats.get("close")))
        return _rows((
            Metric(
                "HULL INTEGRITY", hull, float(max_hull),
                "{0:.0f}/{1}".format(hull, max_hull),
                tone="bad" if hull <= 0 else ("warn" if hull < max_hull else "default"),
            ),
            Metric(
                "CLOSE CALLS", close, max(20.0, close),
                "{0:.0f}".format(close), target=0.0, better="lower",
                tone="default" if close <= 0 else "warn",
            ),
        ))

    return ()


def score_metrics(results=None, missions=3, mission_max=130):
    """Return one bar per mission, including skipped missions as empty rows."""
    results = list(results or [])
    rows = []
    for index in range(max(0, int(missions))):
        result = results[index] if index < len(results) else None
        if isinstance(result, Mapping):
            points = int(_number(result.get("points")))
            display = "{0:+d}".format(points)
            tone = "default" if points > 0 else "bad"
        else:
            points = 0
            display = "SKIP"
            tone = "bad"
        rows.append(Metric(
            "M{0:02d}".format(index + 1),
            max(0, min(mission_max, points)),
            float(mission_max),
            display,
            tone=tone,
        ))
    return tuple(rows)
