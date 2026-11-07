"""IoT Network Node - exploratory / manual-action scenarios (TC-18 .. TC-27).


Run (Wokwi simulator must be running, same as for the main suite):
    pip install pytest pyserial
    pytest -v test_iot_manual_scenarios.py
    RUN_SLOW=1 OUTAGE_SECONDS=300 pytest -v -k tc27 test_iot_manual_scenarios.py
Env: DEVICE_URL (default rfc2217://localhost:4000)

Not automatable over serial (do these by hand in Wokwi): DHT22 value change,
EN/reset button, NET LED timing.
"""
import json, os, re, time
import pytest, serial

URL = os.getenv("DEVICE_URL", "rfc2217://localhost:4000")
STATES = {"DISCONNECTED", "CONNECTING", "CONNECTED", "BACKOFF"}
CAP = 8


class Node:
    def __init__(self):
        self.s = serial.serial_for_url(URL, baudrate=115200, timeout=0.2)
        self.log = []

    def pump(self, secs):
        end = time.time() + secs
        out = []
        while time.time() < end:
            ln = self.s.readline().decode(errors="ignore").strip()
            if ln:
                out.append((time.time(), ln)); self.log.append((time.time(), ln))
        return out

    def raw(self, data: bytes):
        self.s.write(data)

    def cmd(self, c, wait=1.5):
        self.s.reset_input_buffer()
        self.s.write((c + "\n").encode())
        return self.pump(wait)

    def status(self):
        for _, ln in self.cmd("STATUS"):
            m = re.search(r"\{.*\}", ln)
            if m:
                return json.loads(m.group(0))
        pytest.fail("STATUS returned no JSON (node hung?)")

    def reset(self):
        self.cmd("NET UP", 3); self.cmd("RESET STATS", 1)

    def offline_send(self, n):
        self.cmd("NET DOWN", 1)
        ids = []
        for _ in range(n):
            for _, ln in self.cmd("SEND", 0.6):
                m = re.search(r"queued id=(\d+)", ln)
                if m: ids.append(int(m.group(1)))
        return ids

    def retries_in(self, secs):
        return sum(1 for _, l in self.pump(secs) if "[NET] retry=" in l)


def published(lines):
    return [int(m.group(1)) for _, l in lines if (m := re.search(r"publish id=(\d+)", l))]


def rebooted(lines):
    return any("[BOOT]" in l or "rst:0x" in l for _, l in lines)


@pytest.fixture(scope="module")
def node():
    n = Node(); n.pump(1); yield n; n.cmd("NET UP", 1)


@pytest.fixture(autouse=True)
def clean(node):
    node.reset(); yield


# TC-18 R8: BUFFER command must agree with STATUS
@pytest.mark.parametrize("n", [5, 8, 12])
def test_tc18_buffer_cmd_vs_status(node, n):
    node.offline_send(n)
    out = node.cmd("BUFFER", 2)
    text = " ".join(l for _, l in out)
    assert "ERROR" not in text, f"BUFFER rejected: {text}"
    nums = [int(x) for x in re.findall(r"(?:count|size|buffer|occupancy)\D{0,3}(\d+)", text, re.I)]
    if not nums:
        pytest.skip(f"BUFFER output format unknown, send it to QA: {text!r}")
    st = node.status()
    assert nums[0] == st["buffer"], f"BUFFER={nums[0]} but STATUS buffer={st['buffer']}"


# TC-19 R2: double NET DOWN must not double the retry rate or hang the node
def test_tc19_double_net_down(node):
    node.cmd("NET DOWN", 0.5); single = node.retries_in(3)
    node.cmd("NET UP", 3)
    node.raw(b"NET DOWN\nNET DOWN\n"); node.pump(0.5); double = node.retries_in(3)
    print("retries/3s single:", single, "double:", double)
    assert double <= single * 1.5 + 5, f"double NET DOWN multiplied retries: {single} -> {double}"
    assert node.status()["net"] in STATES - {"CONNECTED"}


# TC-20 R1/R2: NET UP while already connected must change nothing
def test_tc20_net_up_when_connected(node):
    before = node.status()
    out = node.cmd("NET UP", 2)
    assert not rebooted(out)
    after = node.status()
    assert after["net"] == "CONNECTED"
    for k in ("buffer", "sent", "dropped", "duplicates", "reconnect_attempts"):
        assert after[k] == before[k], f"{k} changed {before[k]} -> {after[k]}"


# TC-21 R5/R6: connection lost again in the middle of a flush
def test_tc21_net_down_mid_flush(node):
    ids = node.offline_send(8); mark = len(node.log)
    node.raw(b"NET UP\nNET DOWN\n"); node.pump(1.5)
    node.cmd("NET UP", 8)
    pub = published(node.log[mark:])
    dup = {i for i in pub if pub.count(i) > 1}
    assert not dup, f"published more than once: {sorted(dup)}"
    assert set(pub) == set(ids), f"lost: {sorted(set(ids) - set(pub))}"
    st = node.status(); assert st["net"] == "CONNECTED" and st["buffer"] == 0


# TC-22 R5/R6: SEND while the flush is running
def test_tc22_send_during_flush(node):
    ids = node.offline_send(8); mark = len(node.log)
    node.raw(b"NET UP\nSEND\n"); node.pump(6)
    pub = published(node.log[mark:])
    dup = {i for i in pub if pub.count(i) > 1}
    assert not dup, f"published more than once: {sorted(dup)}"
    assert len(set(pub)) == 9, f"expected 8 buffered + 1 new, got {sorted(set(pub))}"
    assert [i for i in pub if i in ids] == sorted(ids), "buffered messages not FIFO"


# TC-23 R1/R7: rapid NET DOWN / NET UP toggling
def test_tc23_rapid_toggle(node):
    h0 = node.status()["heap"]
    for _ in range(15):
        node.cmd("NET DOWN", 0.4); node.cmd("NET UP", 0.6)
    node.pump(3); st = node.status()
    print("heap", h0, "->", st["heap"])
    assert st["net"] == "CONNECTED"
    assert h0 - st["heap"] < 2000, f"heap lost {h0 - st['heap']} B in 15 toggles"


# TC-24 R2: invalid STRESS arguments
@pytest.mark.parametrize("arg", ["-5", "1.5", "abc", "10 20", "99999999999"])
def test_tc24_stress_invalid_args(node, arg):
    out = node.cmd(f"STRESS {arg}", 4)
    assert not rebooted(out), "node rebooted"
    st = node.status(); assert st["heap"] > 0
    if arg in ("-5", "1.5", "abc"):
        assert any("ERROR" in l for _, l in out) or st["sent"] == 0, \
            f"invalid number accepted: sent={st['sent']}"


# TC-25 R2: messy input must not crash or half-execute commands
@pytest.mark.parametrize("line", ["", "   ", "status ", " STATUS", "RESET  STATS", "A" * 300, "NET\tDOWN"])
def test_tc25_messy_input(node, line):
    out = node.cmd(line, 1.5)
    assert not rebooted(out), "node rebooted"
    assert node.status()["net"] in STATES


# TC-26 R3/R8: RESET STATS must clear counters, not buffered data
def test_tc26_reset_stats_keeps_buffer(node):
    node.offline_send(5); before = node.status()["buffer"]
    node.cmd("RESET STATS", 1); st = node.status()
    assert st["buffer"] == before == 5, f"buffer {before} -> {st['buffer']}"
    assert (st["sent"], st["dropped"], st["duplicates"]) == (0, 0, 0)
    assert len(set(published(node.cmd("NET UP", 8)))) == 5, "buffered data lost after RESET STATS"


# TC-27 R2/R7: long outage (slow; RUN_SLOW=1)
@pytest.mark.skipif(os.getenv("RUN_SLOW") != "1", reason="set RUN_SLOW=1 to run the long outage test")
def test_tc27_long_outage(node):
    secs = int(os.getenv("OUTAGE_SECONDS", "300"))
    node.cmd("NET DOWN", 2); s0 = node.status(); node.pump(secs); s1 = node.status()
    print("heap", s0["heap"], "->", s1["heap"], "attempts", s0["reconnect_attempts"], "->", s1["reconnect_attempts"])
    assert not rebooted(node.log[-5000:]), "node rebooted during outage"
    assert abs(s0["heap"] - s1["heap"]) < 1024, "heap changed during a plain outage"
    assert s1["reconnect_attempts"] > s0["reconnect_attempts"] >= 0
    assert s1["reconnect_attempts"] < 2 ** 31