from __future__ import annotations
from collections import defaultdict
from relaygrid.outage.metrics import merge_intervals, interruption_minutes, customer_minutes

class OutageService:
    def __init__(self): self._events=[]
    def add(self,customer_group: str,customers: int,start_min: float,end_min: float):
        if customers<0 or end_min<start_min: raise ValueError("invalid outage")
        self._events.append((customer_group,customers,start_min,end_min))
    def customer_minutes(self):
        return sum(summary["customer_minutes"] for summary in self.group_summaries().values())
    def group_summaries(self):
        grouped=defaultdict(list)
        for group,customers,start,end in self._events:
            grouped[group].append((customers,start,end))
        summaries={}
        for group,events in grouped.items():
            intervals=[(start,end) for _,start,end in events]
            summaries[group]={
                "customers":events[-1][0],
                "intervals":merge_intervals(intervals),
                "minutes":interruption_minutes(intervals),
                "customer_minutes":customer_minutes(events),
            }
        return summaries
