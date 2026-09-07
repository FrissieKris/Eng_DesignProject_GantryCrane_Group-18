"""Parser for the Instrotech 4004/5004 ASCIIbus output frame (manual p.14).

Frame: # AA S DDDDDDDD P CR LF  (13 chars before CR/LF)
  AA = unit address (00-99), S = sign, D = 8 numeral chars (left-padded
  with spaces on the 4004/5004 since the protocol reserves 8 digits for
  future models), P = number of decimal places, matching the display.
"""
import re

FRAME_RE = re.compile(r"^#(?P<addr>\d{2})(?P<sign>[+-])(?P<data>[ \d]{8})(?P<dp>\d)$")


def parse_frame(line: str):
    """Return (address: int, value: float) or None if the line isn't a valid frame."""
    line = line.strip("\r\n")
    m = FRAME_RE.match(line)
    if not m:
        return None
    data_str = m.group("data").strip()
    if not data_str.isdigit():
        # Overrange / underrange conditions don't map to a clean numeral field.
        return None
    sign = 1 if m.group("sign") == "+" else -1
    dp = int(m.group("dp"))
    value = sign * int(data_str) / (10 ** dp)
    return int(m.group("addr")), value
