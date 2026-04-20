"""
Persistent storage for signals.
Data is saved as JSON in data/signals.json
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

STORAGE_FILE = os.path.join("data", "signals.json")
EMA_ALPHA = 0.1
MAX_INTERVAL_HISTORY = 20


def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def _load_raw() -> Dict:
    _ensure_data_dir()
    if not os.path.exists(STORAGE_FILE):
        return {"signals": []}
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"signals": []}


def _save_raw(data: Dict):
    _ensure_data_dir()
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def record_signal(signal_dict: Dict):
    """Append a new signal to persistent history."""
    data = _load_raw()
    signals = data.get("signals", [])
    signals.append(signal_dict)
    # Keep only last MAX_INTERVAL_HISTORY*2 entries to avoid unlimited growth
    if len(signals) > MAX_INTERVAL_HISTORY * 2:
        signals = signals[-MAX_INTERVAL_HISTORY * 2:]
    data["signals"] = signals
    _save_raw(data)


def get_last_signal_time() -> Optional[datetime]:
    data = _load_raw()
    signals = data.get("signals", [])
    if not signals:
        return None
    last = signals[-1]
    ts_str = last.get("timestamp")
    if ts_str:
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except:
            return None
    return None


def get_time_since_last_signal() -> float:
    """Minutes since last recorded signal."""
    last_time = get_last_signal_time()
    if last_time is None:
        return 0.0
    delta = datetime.utcnow() - last_time
    return max(0.0, delta.total_seconds() / 60.0)


def get_avg_interval() -> float:
    """Exponential moving average of intervals between signals."""
    data = _load_raw()
    signals = data.get("signals", [])
    if len(signals) < 2:
        return 120.0  # default

    # Compute intervals in minutes
    intervals = []
    for i in range(1, len(signals)):
        try:
            t1 = datetime.fromisoformat(signals[i-1]["timestamp"].replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(signals[i]["timestamp"].replace("Z", "+00:00"))
            interval = (t2 - t1).total_seconds() / 60.0
            intervals.append(interval)
        except:
            continue

    if not intervals:
        return 120.0

    # EMA of intervals
    ema = intervals[0]
    for val in intervals[1:]:
        ema = EMA_ALPHA * val + (1 - EMA_ALPHA) * ema
    return ema


def get_estimated_next_signal() -> float:
    """Minutes until next signal based on average interval."""
    avg = get_avg_interval()
    elapsed = get_time_since_last_signal()
    return max(0.0, avg - elapsed)
