"""HW7 IoT Network Testing - pytest suite (R1-R8).
Run: start Wokwi simulator, then:  pytest -v test_iot_network.py
Env: DEVICE_URL (default rfc2217://localhost:4000)  pip install pytest pyserial
"""
import json, os, re, time
import pytest, serial

URL = os.getenv("DEVICE_URL", "rfc2217://localhost:4000")
STATES = {"DISCONNECTED", "CONNECTING", "CONNECTED", "BACKOFF"}
CAP = 8


class Node:
    def __init__(self):
        self.s = serial.serial_for_url(URL, baudrate=115200, timeout=0.2)
        self.log = []                       # (t, line)

    def pump(self, secs):
        end = time.time() + secs
        out = []
        while time.time() < end:
            ln = self.s.readline().decode(errors="ignore").strip()
            if ln:
                out.append((time.time(), ln)); self.log.append((time.time(), ln))
        return out

    def cmd(self, c, wait=1.5):
        self.s.reset_input_buffer()
        self.s.write((c + "\n").encode())
        return self.pump(wait)

    def status(self):
        for _, ln in self.cmd("STATUS"):
            m = re.search(r"\{.*\}", ln)
            if m:
                return json.loads(m.group(0))
        pytest.fail("STATUS returned no JSON (node hung or R8 violated)")

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

    def recover(self, secs=6):
        return self.pump(0) or self.cmd("NET UP", secs)


@pytest.fixture(scope="module")
def node():
    n = Node(); n.pump(1); yield n; n.cmd("NET UP", 1)


@pytest.fixture(autouse=True)
def clean(node):
    node.reset(); yield


def published(lines):
    return [int(m.group(1)) for _, l in lines if (m := re.search(r"publish id=(\d+)", l))]


# TC-01 R1 states observable
def test_tc01_states_observable(node):
    node.cmd("NET DOWN", 8); log = node.log[-80:]
    seen = {m.group(1) for _, l in log if (m := re.search(r"\[NET\] state=(\w+)", l))}
    assert seen <= STATES and seen, f"unexpected/no states: {seen}"
    assert seen & {"DISCONNECTED", "BACKOFF", "CONNECTING"}
    up = node.cmd("NET UP", 6)
    assert node.status()["net"] == "CONNECTED"


# TC-02 R2 no hang during outage
def test_tc02_no_hang_in_outage(node):
    node.cmd("NET DOWN", 12)
    assert node.status()["net"] in STATES - {"CONNECTED"}


# TC-03 R2 backoff, no reconnect storm
def test_tc03_backoff_no_storm(node):
    out = node.cmd("NET DOWN", 20)
    ts = [t for t, l in out if "[NET] retry=" in l]
    assert ts, "no retry lines after NET DOWN"
    assert len(ts) <= 12, f"{len(ts)} retries in 20s = reconnect storm"
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    assert all(g >= 0.5 for g in gaps), f"gaps too small: {gaps}"
    bo = [int(m.group(1)) for _, l in out if (m := re.search(r"backoff_ms=(\d+)", l))]
    assert bo == sorted(bo) and bo[-1] > bo[0], f"backoff not growing: {bo}"
    assert node.status()["reconnect_attempts"] == len(ts)


# TC-04 R3 offline buffering
def test_tc04_offline_buffer(node):
    ids = node.offline_send(5)
    assert len(ids) == 5 and len(set(ids)) == 5
    st = node.status(); assert st["buffer"] == 5 and st["capacity"] == CAP and st["sent"] == 0


# TC-05 R5 recovery flush
def test_tc05_recovery_flush(node):
    ids = node.offline_send(5)
    out = node.cmd("NET UP", 8)
    assert sorted(published(out)) == sorted(ids)
    st = node.status(); assert st["net"] == "CONNECTED" and st["buffer"] == 0 and st["sent"] == 5


# TC-06 R4 overflow 12 -> 8 buffered, 4 dropped, logged
def test_tc06_overflow_counters(node):
    node.offline_send(12)
    st = node.status()
    assert st["buffer"] == CAP and st["dropped"] == 4
    assert any("overflow policy=DROP_OLDEST" in l for _, l in node.log[-80:])


# TC-07 R4 DROP_OLDEST: newest 8 survive
def test_tc07_drop_oldest_order(node):
    ids = node.offline_send(12)
    assert published(node.cmd("NET UP", 10)) == ids[-CAP:]


# TC-08 R4 boundary == 8
def test_tc08_boundary_8(node):
    node.offline_send(8); st = node.status()
    assert st["buffer"] == 8 and st["dropped"] == 0


# TC-09 R4 boundary 9
def test_tc09_boundary_9(node):
    ids = node.offline_send(9); st = node.status()
    assert st["buffer"] == 8 and st["dropped"] == 1
    assert published(node.cmd("NET UP", 8)) == ids[1:]


# TC-10 R6 no duplicate publish IDs
def test_tc10_no_duplicate_ids(node):
    node.offline_send(8)
    pub = published(node.cmd("NET UP", 10))
    assert len(pub) == len(set(pub)), f"duplicate IDs: {pub}"
    assert node.status()["duplicates"] == 0


# TC-11 R6/R8 counter consistency: sent == generated - dropped
def test_tc11_sent_consistency(node):
    node.offline_send(12); node.cmd("NET UP", 10)
    st = node.status()
    assert st["sent"] == 12 - st["dropped"] == 8


# TC-12 R7 heap trend over 10 x STRESS 100
def test_tc12_heap_stability(node):
    heaps = [node.status()["heap"]]
    for _ in range(10):
        node.cmd("STRESS 100", 6); heaps.append(node.status()["heap"])
    drops = [a - b for a, b in zip(heaps, heaps[1:])]
    print("heap:", heaps, "bytes/msg:", [d / 100 for d in drops])
    assert not all(d > 0 for d in drops), "heap fell on every iteration"
    assert heaps[0] - heaps[-1] < 0.05 * heaps[0], "heap lost >5%"


# TC-13 R7/R4 stress while offline
def test_tc13_stress_offline(node):
    node.cmd("NET DOWN", 1); node.cmd("STRESS 100", 8); st = node.status()
    assert st["buffer"] <= CAP and st["dropped"] == 100 - CAP


# TC-14 R8 STATUS evidence fields
def test_tc14_status_fields(node):
    need = {"net", "broker", "buffer", "capacity", "sent", "dropped",
            "duplicates", "reconnect_attempts", "heap"}
    assert need <= set(node.status())


# TC-15 RESET STATS zeroes counters
def test_tc15_reset_stats(node):
    node.offline_send(10); node.cmd("RESET STATS", 1); st = node.status()
    assert (st["sent"], st["dropped"], st["duplicates"], st["reconnect_attempts"]) == (0, 0, 0, 0)


# TC-16 negative: invalid commands do not break node
@pytest.mark.parametrize("bad", ["status", "STRESS", "FOO"])
def test_tc16_invalid_commands(node, bad):
    out = node.cmd(bad, 1.5)
    assert any("ERROR" in l for _, l in out)
    assert node.status()["net"] in STATES


# TC-17 exploratory: STRESS range 1-500 (manual); behaviour outside range
@pytest.mark.parametrize("n", [0, 501])
def test_tc17_stress_out_of_range(node, n):
    node.cmd(f"STRESS {n}", 4)
    assert node.status()["heap"] > 0   # must stay alive, no crash/reboot
