"""Pure image-row extraction and conservative tracking of the player's HP bar.

An ambiguous observation is never promoted to a player position. In particular,
another player's bar cannot silently replace a lost track.
"""
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np


@dataclass(frozen=True)
class Bar:
    x_start: int
    x_end: int
    y: int
    clipped: bool = False

    @property
    def width(self):
        return self.x_end - self.x_start + 1

    @property
    def center(self):
        return (self.x_start + self.x_end) / 2

    def as_dict(self):
        return {"x_start": self.x_start, "x_end": self.x_end,
                "y": self.y, "width": self.width, "clipped": self.clipped}


def red_intervals(rgb_row, y, *, r_min, r_max, g_max, b_max,
                  rg_ratio, rb_ratio, gap):
    """Extract bars from one RGB row without processing the whole screenshot."""
    if len(rgb_row) == 0:
        return []
    r = rgb_row[:, 0].astype(np.float32)
    g = rgb_row[:, 1].astype(np.float32)
    b = rgb_row[:, 2].astype(np.float32)
    indices = np.flatnonzero((r >= r_min) & (r <= r_max) & (g < g_max)
                             & (b < b_max) & (r > g * rg_ratio)
                             & (r > b * rb_ratio))
    if not len(indices):
        return []
    splits = np.flatnonzero(np.diff(indices) > max(1, gap)) + 1
    groups = np.split(indices, splits)
    width = len(rgb_row)
    return [Bar(int(group[0]), int(group[-1]), y,
                int(group[0]) == 0 or int(group[-1]) == width - 1)
            for group in groups]


class PlayerBarTracker:
    """Track one observed bar. Lost or merged bars yield no position."""

    def __init__(self, min_width, max_width, tolerance, seed_x=None):
        self.min_width = min_width
        self.max_width = max_width
        self.tolerance = tolerance
        self.seed_x = seed_x
        self.position: Optional[float] = None
        self.velocity = 0.0
        self.misses = 0
        self.status = "uninitialized"
        self.occluded_identity = False

    def reset(self, seed_x=None):
        self.position = None
        self.velocity = 0.0
        self.misses = 0
        self.seed_x = seed_x
        self.status = "uninitialized"
        self.occluded_identity = False

    def observe(self, bars: Sequence[Bar], exclude_range=None) -> Optional[Bar]:
        complete = [b for b in bars if not b.clipped
                    and self.min_width <= b.width <= self.max_width]
        # A merged pair is wider than one bar. Treat it as occlusion, not as a
        # new position or evidence that the character left the scene.
        merged = [b for b in bars if b.width > self.max_width]
        predicted = self.position
        if predicted is None:
            predicted = self.seed_x
        elif self.misses == 0:
            predicted += self.velocity

        if predicted is None:
            if len(complete) != 1:
                return self._miss("ambiguous" if bars else "missing")
            candidate = complete[0]
            if exclude_range and exclude_range[0] <= candidate.x_start <= exclude_range[1]:
                return self._miss("ambiguous")
        else:
            gate = self.tolerance if self.position is not None else self.max_width
            ranked = sorted(((abs(b.x_start - predicted), b) for b in complete),
                            key=lambda item: item[0])
            if self.occluded_identity and sum(distance <= gate for distance, _ in ranked) > 1:
                return self._miss("ambiguous")
            if not ranked or ranked[0][0] > gate:
                return self._miss("occluded" if bars else "missing")
            distance, candidate = ranked[0]
            # Close competing bars have no reliable identity after crossing.
            if len(ranked) > 1 and ranked[1][0] - distance < self.min_width / 2:
                return self._miss("ambiguous")
            # If a merged or clipped interval covers the predicted position,
            # a nearby separate bar might belong to another player.
            if any(b.x_start - self.max_width <= predicted <= b.x_end + self.max_width
                   for b in merged if b is not candidate):
                return self._miss("occluded")
            if any(b.clipped and b.x_start - self.max_width <= predicted <= b.x_end + self.max_width
                   for b in bars):
                return self._miss("occluded")
            if (exclude_range and exclude_range[0] <= candidate.x_start <= exclude_range[1]
                    and self.position is None):
                return self._miss("ambiguous")

        if self.position is not None:
            self.velocity = max(-self.tolerance, min(self.tolerance,
                                                    candidate.x_start - self.position))
        self.position = float(candidate.x_start)
        self.seed_x = None
        self.misses = 0
        self.status = "tracked"
        self.occluded_identity = False
        return candidate

    def _miss(self, status):
        self.misses += 1
        self.status = status
        if status in ("ambiguous", "occluded"):
            self.occluded_identity = True
        # Keep the identity through temporary occlusion. Do not re-acquire
        # another bar automatically after a timeout.
        self.velocity = 0.0
        return None
