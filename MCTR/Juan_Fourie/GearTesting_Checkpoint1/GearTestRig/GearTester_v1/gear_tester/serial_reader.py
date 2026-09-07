import queue
import threading
import time
from datetime import datetime

import serial

from .protocol import parse_frame


class SerialReader(threading.Thread):
    """Background thread that reads ASCIIbus frames and pushes them to a queue.

    Retries the connection instead of dying on a transient RS485/USB hiccup,
    since a UTS-style test can run unattended for a while.
    """

    def __init__(self, port, baud, address_filter=None, demand_mode=False, poll_hz=5.0):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.address_filter = address_filter
        self.demand_mode = demand_mode
        self.poll_interval = 1.0 / poll_hz if poll_hz else 0.2
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        self.error_count = 0
        self.connected = False

    def stop(self):
        self._stop_event.set()

    def run(self):
        retry_delay = 2.0
        while not self._stop_event.is_set():
            try:
                self._run_once()
            except serial.SerialException as e:
                self.connected = False
                self.queue.put(("error", f"Serial error: {e}"))
            if self._stop_event.is_set():
                return
            self.queue.put(("warning", f"Reconnecting to {self.port} in {retry_delay:.0f}s..."))
            self._stop_event.wait(retry_delay)

    def _run_once(self):
        with serial.Serial(
            port=self.port,
            baudrate=self.baud,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.2,
        ) as ser:
            self.connected = True
            self.queue.put(("info", f"Connected to {self.port} @ {self.baud} baud"))
            last_poll = 0.0
            while not self._stop_event.is_set():
                if self.demand_mode:
                    now = time.monotonic()
                    if now - last_poll >= self.poll_interval:
                        ser.write(b"?")
                        last_poll = now
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("ascii", errors="ignore")
                result = parse_frame(line)
                if result is None:
                    self.error_count += 1
                    continue
                addr, value = result
                if self.address_filter is not None and addr != self.address_filter:
                    continue
                self.queue.put(("sample", datetime.now(), value))
        self.connected = False
