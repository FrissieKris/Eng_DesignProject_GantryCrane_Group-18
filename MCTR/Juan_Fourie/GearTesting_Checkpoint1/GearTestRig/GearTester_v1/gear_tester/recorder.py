import csv
import os
import re
import time
from datetime import datetime


def safe_filename(label: str) -> str:
    label = label.strip() or "test"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", label)


class Recording:
    """One start-to-stop capture, written to CSV incrementally so a crash
    mid-test doesn't lose data. Tracks peak load and flags a probable
    break so the dashboard can decide when to auto-stop.
    """

    def __init__(self, log_dir, label, units, break_frac, break_min_load,
                 confirm_samples, tail_samples, auto_stop):
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"{safe_filename(label)}_{ts}.csv")
        self.units = units
        self.break_frac = break_frac
        self.break_min_load = break_min_load
        self.confirm_samples = confirm_samples
        self.tail_samples = tail_samples
        self.auto_stop = auto_stop

        self._file = open(self.path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(["sample_no", "elapsed_s", "timestamp", f"load_{units}"])

        self.start_time = time.monotonic()
        self.sample_no = 0
        self.peak = float("-inf")
        self.break_streak = 0
        self.break_confirmed = False
        self.tail_remaining = 0
        self.finished_reason = None  # set once ready to stop

    def add_sample(self, ts: datetime, value: float):
        self.sample_no += 1
        elapsed = time.monotonic() - self.start_time
        self._writer.writerow([self.sample_no, f"{elapsed:.3f}", ts.isoformat(timespec="milliseconds"), value])
        self._file.flush()
        self.peak = max(self.peak, value)

        if not self.auto_stop or self.finished_reason:
            return
        dropped = self.peak >= self.break_min_load and value <= self.peak * (1 - self.break_frac)
        self.break_streak = self.break_streak + 1 if dropped else 0
        if self.break_streak >= self.confirm_samples and not self.break_confirmed:
            self.break_confirmed = True
            self.tail_remaining = self.tail_samples
        elif self.break_confirmed:
            if self.tail_remaining > 0:
                self.tail_remaining -= 1
            else:
                self.finished_reason = "break detected"

    def close(self, reason="manual stop"):
        self._file.close()
        return {
            "path": self.path,
            "samples": self.sample_no,
            "peak": self.peak if self.sample_no else 0.0,
            "duration_s": time.monotonic() - self.start_time,
            "reason": reason,
        }
