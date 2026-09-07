import argparse
import ctypes
import os
import queue
import sys
import time

from .recorder import Recording
from .serial_reader import SerialReader

BAUD_CHOICES = [2400, 4800, 9600, 19200]


def _enable_vt_mode():
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def _clear():
    sys.stdout.write("\x1b[H\x1b[J")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Live console dashboard for the Instrotech 4004/5004 load cell indicator")
    p.add_argument("--port", required=True, help="COM port the RS485-USB converter enumerates as, e.g. COM3")
    p.add_argument("--baud", type=int, default=9600, choices=BAUD_CHOICES)
    p.add_argument("--address", type=int, default=None,
                    help="Only accept frames from this indicator address (01-99). Omit to accept any.")
    p.add_argument("--demand-mode", action="store_true",
                    help="Use if the indicator's unit address is set to 00 (on-demand); polls it instead of "
                         "relying on continuous streaming.")
    p.add_argument("--poll-hz", type=float, default=5.0, help="Poll rate when --demand-mode is used")
    p.add_argument("--units", default="kg")
    p.add_argument("--log-dir", default="logs")
    p.add_argument("--break-frac", type=float, default=0.20,
                    help="Fractional drop from peak load that counts as a break (default 0.20 = 20%%)")
    p.add_argument("--break-min-load", type=float, default=5.0,
                    help="Peak load that must be reached before break-detection arms, to ignore near-zero noise")
    p.add_argument("--confirm-samples", type=int, default=3,
                    help="Consecutive dropped samples required to confirm a break")
    p.add_argument("--tail-samples", type=int, default=5,
                    help="Extra samples captured after a break is confirmed, before auto-stop")
    p.add_argument("--no-auto-stop", action="store_true",
                    help="Disable automatic stop-on-break; recording only ever stops on 'x' or 'q' "
                         "(use for gears you expect not to fail)")
    return p.parse_args(argv)


def render(args, status_msg, connected, latest_value, latest_ts, current, error_count):
    _clear()
    lines = []
    lines.append("=== Load Cell Dashboard - Instrotech 4004/5004 ===")
    lines.append(f"Port: {args.port}  Baud: {args.baud}  Connected: {'yes' if connected else 'no'}  "
                  f"Frame errors: {error_count}")
    lines.append("")
    if latest_value is None:
        lines.append("Live reading: --waiting for data--")
    else:
        lines.append(f"Live reading: {latest_value:10.3f} {args.units}   (at {latest_ts:%H:%M:%S})")
    lines.append("")
    if current is None:
        lines.append("Recording:    STOPPED")
    else:
        elapsed = time.monotonic() - current.start_time
        lines.append(f"Recording:    RUNNING -> {current.path}")
        lines.append(f"  Samples: {current.sample_no}   Elapsed: {elapsed:6.1f}s   "
                      f"Peak: {current.peak if current.sample_no else 0.0:.3f} {args.units}")
        if current.break_confirmed:
            lines.append("  Break detected - capturing tail samples before auto-stop...")
    lines.append("")
    lines.append(f"Auto-stop on break: {'off' if args.no_auto_stop else 'on'} "
                 f"(drop >= {args.break_frac*100:.0f}% from peak, peak >= {args.break_min_load} {args.units})")
    lines.append("")
    lines.append("[s] start recording   [x] stop & save   [a] toggle auto-stop   [q] quit")
    if status_msg:
        lines.append("")
        lines.append(f"> {status_msg}")
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


def main(argv=None):
    args = parse_args(argv)
    _enable_vt_mode()

    try:
        import msvcrt
    except ImportError:
        print("This dashboard uses msvcrt for keyboard input and only runs on Windows.")
        return 1

    reader = SerialReader(args.port, args.baud, address_filter=args.address,
                           demand_mode=args.demand_mode, poll_hz=args.poll_hz)
    reader.start()

    current = None
    latest_value = None
    latest_ts = None
    status_msg = ""
    last_draw = 0.0

    try:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode(errors="ignore").lower()
                if key == "q":
                    break
                elif key == "s":
                    if current is not None:
                        status_msg = "Already recording - press 'x' to stop it first."
                    else:
                        sys.stdout.write("\nGear / test label (Enter for default): ")
                        sys.stdout.flush()
                        label = input().strip() or "gear"
                        current = Recording(
                            args.log_dir, label, args.units,
                            break_frac=args.break_frac, break_min_load=args.break_min_load,
                            confirm_samples=args.confirm_samples, tail_samples=args.tail_samples,
                            auto_stop=not args.no_auto_stop,
                        )
                        status_msg = f"Recording started: {current.path}"
                elif key == "x":
                    if current is None:
                        status_msg = "Not recording."
                    else:
                        summary = current.close(reason="manual stop")
                        status_msg = (f"Saved {summary['samples']} samples to {summary['path']} "
                                      f"(peak {summary['peak']:.3f} {args.units}, "
                                      f"{summary['duration_s']:.1f}s, {summary['reason']})")
                        current = None
                elif key == "a":
                    args.no_auto_stop = not args.no_auto_stop
                    status_msg = f"Auto-stop on break: {'off' if args.no_auto_stop else 'on'}"

            drained = False
            while True:
                try:
                    item = reader.queue.get_nowait()
                except queue.Empty:
                    break
                drained = True
                tag = item[0]
                if tag == "sample":
                    _, ts, value = item
                    latest_value, latest_ts = value, ts
                    if current is not None and current.finished_reason is None:
                        current.add_sample(ts, value)
                else:
                    status_msg = item[1]

            if current is not None and current.finished_reason:
                summary = current.close(reason=current.finished_reason)
                status_msg = (f"AUTO-STOPPED: saved {summary['samples']} samples to {summary['path']} "
                              f"(peak {summary['peak']:.3f} {args.units}, "
                              f"{summary['duration_s']:.1f}s, {summary['reason']})")
                current = None

            now = time.monotonic()
            if drained or now - last_draw > 0.15:
                render(args, status_msg, reader.connected, latest_value, latest_ts, current, reader.error_count)
                last_draw = now

            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        if current is not None:
            summary = current.close(reason="interrupted")
            print(f"\nSaved {summary['samples']} samples to {summary['path']} before exit.")
        reader.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
