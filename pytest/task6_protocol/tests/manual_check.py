"""Sync-safe manual checks: python manual_check.py [port]

Why a new version: the first manual_check.py used a 1 s timeout. PING answers
later than that, so late replies were read as answers to the NEXT command and
the whole log was shifted by one command. Here every step
  - waits up to 5 s for the answer and prints the measured latency,
  - drains late replies before the next step,
  - checks that the reply really belongs to the command (flags DESYNC otherwise).
Saves evidence/manual_check.log."""
import os
import sys
from pathlib import Path

from device import Device

PORT = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DEVICE_PORT")
if not PORT:
    sys.exit("Usage: python manual_check.py rfc2217://localhost:4000")

# command -> text that must be in the reply for it to belong to that command
EXPECT = {
    "PING": '"command":"PING"', "STATUS": '"heap"', "GET TEMP": '"temperature"',
    "SET LED": '"led"', "SET PWM": '"pwm"', "RESET": '"reset"',
}

STEPS = [
    ("PING x5: how late is the answer?", ["PING"] * 5),
    ("GET TEMP x3: is the closing brace always missing?", ["GET TEMP"] * 3),
    ("PWM boundary", ["SET PWM 99", "SET PWM 100", "SET PWM 101", "STATUS"]),
    ("PWM scale in STATUS", ["SET PWM 1", "STATUS", "SET PWM 50", "STATUS", "SET PWM 99", "STATUS"]),
    ("RESET after LED ON and PWM 50", ["SET LED ON", "SET PWM 50", "STATUS", "RESET", "STATUS"]),
    ("Unknown command", ["FOO"]),
    ("NO_RESPONSE (must time out)", ["NO_RESPONSE"]),
]


def belongs(cmd, reply):
    for prefix, marker in EXPECT.items():
        if cmd.startswith(prefix):
            return marker in reply or '"ERROR"' in reply
    return True


dev = Device(PORT, timeout=5.0)
print("READY banner seen:", dev.wait_ready(2.0))
for title, commands in STEPS:
    print(f"\n--- {title}")
    dev.drain(2.0)  # let late replies from the previous step arrive and be dropped
    for cmd in commands:
        try:
            reply = dev.command_raw(cmd, timeout=5.0)
            flag = "" if belongs(cmd, reply) else "   <-- DESYNC (reply does not match command)"
            print(f"{cmd:<12} -> {reply}  [{dev.last_elapsed:.2f}s]{flag}")
        except TimeoutError:
            print(f"{cmd:<12} -> NO ANSWER within 5 s")
            dev.drain(2.0)
dev.drain(2.0)
for cmd in ("RESET", "SET LED OFF", "SET PWM 0"):
    try:
        dev.command_raw(cmd, timeout=5.0)
    except TimeoutError:
        pass
Path("evidence").mkdir(exist_ok=True)
Path("evidence/manual_check.log").write_text("\n".join(dev.transcript) + "\n", encoding="utf-8")
dev.close()
print("\nSaved evidence/manual_check.log")
