from dataclasses import dataclass

@dataclass
class Thresholds:
    idle_cpu_pct: float = 5.0
    underutil_cpu_pct: float = 20.0
    min_hours_active: float = 100.0
    min_cost_consider: float = 5.0
    rightsizing_savings_pct: float = 0.35
    idle_stop_savings_pct: float = 0.90
    storage_cold_days: int = 30
    storage_savings_pct: float = 0.40
