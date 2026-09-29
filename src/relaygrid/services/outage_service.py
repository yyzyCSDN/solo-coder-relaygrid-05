from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from relaygrid.outage.metrics import merge_intervals, interruption_minutes

@dataclass(frozen=True)
class _OutageEvent:
    # The customer count is captured when the event is recorded so later
    # additions to the same customer group cannot retroactively rewrite
    # earlier outages.
    sequence: int
    customers: int
    start_min: float
    end_min: float


def _group_minutes(events: list[_OutageEvent]) -> float:
    """Customer-minutes for one group, using each event's frozen headcount.

    Overlapping events are not double counted: each segment of the merged
    outage interval is weighted by the headcount frozen on the earliest
    event covering that segment.
    """
    # Sweep over every segment boundary; within each segment the active event
    # set is constant.
    boundaries = sorted({b for e in events for b in (e.start_min, e.end_min)})
    total = 0.0
    for seg_start, seg_end in zip(boundaries, boundaries[1:]):
        if seg_end <= seg_start:
            continue
        active = [
            e for e in events
            if e.start_min <= seg_start and e.end_min >= seg_end
        ]
        if not active:
            continue
        governing = min(active, key=lambda e: (e.start_min, e.sequence))
        total += governing.customers * (seg_end - seg_start)
    return total


class OutageService:
    def __init__(self):
        self._events: defaultdict[str, list[_OutageEvent]] = defaultdict(list)
        self._next_sequence = 0

    def add(self, customer_group: str, customers: int, start_min: float, end_min: float):
        if customers < 0 or end_min < start_min:
            raise ValueError("invalid outage")
        self._events[customer_group].append(
            _OutageEvent(self._next_sequence, customers, start_min, end_min)
        )
        self._next_sequence += 1

    def group_summaries(self):
        summaries = {}
        for group, events in self._events.items():
            intervals = merge_intervals(
                [(e.start_min, e.end_min) for e in events]
            )
            # Frozen headcount for the group: the count recorded when the
            # earliest outage began, not the most recently added one.
            earliest = min(events, key=lambda e: (e.start_min, e.sequence))
            summaries[group] = {
                "customers": earliest.customers,
                "intervals": intervals,
                "minutes": interruption_minutes(
                    [(e.start_min, e.end_min) for e in events]
                ),
                "customer_minutes": _group_minutes(events),
            }
        return summaries

    def customer_minutes(self):
        # The grand total is derived from the group summaries so it can never
        # disagree with per-group accounting.
        return sum(g["customer_minutes"] for g in self.group_summaries().values())
