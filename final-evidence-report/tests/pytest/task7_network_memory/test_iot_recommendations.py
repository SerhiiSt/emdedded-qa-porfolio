"""IoT Network Node - fix-verification tests, one group per QA recommendation (REC-1 .. REC-6).
Expected: FAIL on the current buggy firmware (each failure maps to a bug), PASS after the fix.
Self-contained; does not import the other suites.

Run (Wokwi running):
    pip install pytest pyserial
    pytest -v test_iot_recommendations.py          # all
    pytest -v -k rec3 test_iot_recommendations.py  # one recommendation
Env: DEVICE_URL (default rfc2217://localhost:4000)

REC-1 buffer capacity + DROP_OLDEST   (BUG-03)
REC-2 flush: once, FIFO, no phantoms  (BUG-02, BUG-05)
REC-3 no memory leak                  (BUG-04)
REC-4 exponential backoff             (BUG-01)
REC-5 counters match the log          (R8)
REC-6 input validation, idempotency   (BUG-06, BUG-07)
Assumptions (not in requirements): REC-3 limit 4 B/message; REC-4 needs >=3 distinct backoff
values in 20 s and CONNECTED within 3 s of NET UP; REC-6 STRESS 0 / 501 must give [CLI] ERROR.
"""
import json, os, re, time
import pytest, serial

URL = os.getenv("DEVICE_URL", "rfc2217://localhost:4000")
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


def published(lines):
    return [int(m.group(1)) for _, l in lines if (m := re.search(r"publish id=(\d+)", l))]


def retries(lines):
    return [(t, int(m.group(1))) for t, l in lines if (m := re.search(r"\[NET\] retry=\d+ backoff_ms=(\d+)", l))]


@pytest.fixture(scope="module")
def node():
    n = Node(); n.pump(1); yield n; n.cmd("NET UP", 1)


@pytest.fixture(autouse=True)
def clean(node):
    node.reset(); yield


# ---------------------------------------------------------------- REC-1
def test_rec1a_buffer_never_exceeds_capacity(node):
    node.offline_send(12)
    st = node.status()
    assert st["buffer"] <= CAP, f"STATUS buffer={st['buffer']}"
    out = node.cmd("BUFFER", 2)
    nums = [int(m.group(1)) for _, l in out if (m := re.search(r"\[BUFFER\] count=(\d+)", l))]
    assert nums and nums[0] <= CAP, f"BUFFER output: {[l for _, l in out]}"


def test_rec1b_dropped_counter_and_log(node):
    node.offline_send(12)
    assert node.status()["dropped"] == 4
    totals = [int(m.group(1)) for _, l in node.log[-200:] if (m := re.search(r"dropped_total=(\d+)", l))]
    assert totals and totals[-1] == 4, f"dropped_total in log: {totals}"


def test_rec1c_oldest_dropped_newest_kept(node):
    ids = node.offline_send(12)
    assert published(node.cmd("NET UP", 10)) == ids[-CAP:]


def test_rec1d_stress_offline_100(node):
    node.cmd("NET DOWN", 1); node.cmd("STRESS 100", 8); st = node.status()
    assert st["buffer"] <= CAP and st["dropped"] == 100 - CAP, st


# ---------------------------------------------------------------- REC-2
def test_rec2a_each_buffered_message_published_once(node):
    ids = node.offline_send(5)
    pub = published(node.cmd("NET UP", 8))
    assert sorted(pub) == sorted(ids), f"queued {ids}, published {pub}"


def test_rec2b_flush_is_fifo(node):
    ids = node.offline_send(8)
    assert published(node.cmd("NET UP", 8)) == ids


def test_rec2c_buffer_empty_and_sent_correct_after_flush(node):
    node.offline_send(8); node.cmd("NET UP", 8)
    st = node.status()
    assert st["net"] == "CONNECTED" and st["buffer"] == 0 and st["sent"] == 8, st


def test_rec2d_no_phantom_ids(node):
    ids = node.offline_send(10)
    pub = published(node.cmd("NET UP", 10))
    assert set(pub) <= set(ids), f"never queued: {sorted(set(pub) - set(ids))}"


def test_rec2e_flush_after_overflow(node):
    ids = node.offline_send(12)
    pub = published(node.cmd("NET UP", 10))
    assert pub == ids[-CAP:], f"expected {ids[-CAP:]}, got {pub}"


# ---------------------------------------------------------------- REC-3
def test_rec3a_no_leak_in_stress(node):
    heaps = [node.status()["heap"]]
    for _ in range(5):
        node.cmd("STRESS 100", 6); heaps.append(node.status()["heap"])
    per_msg = [(a - b) / 100 for a, b in zip(heaps, heaps[1:])]
    print("bytes/msg:", per_msg)
    assert max(per_msg) < 4, f"leak {per_msg} B/message"


def test_rec3b_no_leak_in_buffer_flush_cycles(node):
    h0 = node.status()["heap"]
    for _ in range(5):
        node.offline_send(8); node.cmd("NET UP", 6)
    h1 = node.status()["heap"]
    print("heap", h0, "->", h1)
    assert h0 - h1 < 500, f"heap lost {h0 - h1} B in 5 buffer/flush cycles"


# ---------------------------------------------------------------- REC-4
def test_rec4a_backoff_grows(node):
    bo = [b for _, b in retries(node.cmd("NET DOWN", 20))]
    assert bo, "no retry lines"
    assert bo == sorted(bo), f"backoff decreases: {bo[:10]}"
    assert len(set(bo)) >= 3, f"backoff does not grow: {sorted(set(bo))}"


def test_rec4b_no_reconnect_storm(node):
    n = len(retries(node.cmd("NET DOWN", 20)))
    assert n <= 12, f"{n} retries in 20 s"


def test_rec4c_interval_respects_backoff(node):
    r = retries(node.cmd("NET DOWN", 15))
    assert len(r) >= 2
    for (t0, b0), (t1, _) in zip(r, r[1:]):
        assert t1 - t0 >= 0.8 * b0 / 1000 - 0.03, f"gap {t1 - t0:.3f}s < backoff {b0} ms"


def test_rec4d_recovers_fast_after_net_up(node):
    node.cmd("NET DOWN", 15)
    t0 = time.time(); node.s.write(b"NET UP\n")
    out = node.pump(4)
    hit = [t for t, l in out if "state=CONNECTED" in l]
    assert hit and hit[0] - t0 <= 3, "not CONNECTED within 3 s of NET UP"


# ---------------------------------------------------------------- REC-5
def test_rec5a_sent_plus_dropped_equals_generated(node):
    node.offline_send(12); node.cmd("NET UP", 10)
    st = node.status()
    assert (st["sent"], st["dropped"]) == (8, 4), st


def test_rec5b_sent_equals_publish_lines(node):
    node.offline_send(8)
    pub = published(node.cmd("NET UP", 8))
    assert node.status()["sent"] == len(pub)


def test_rec5c_duplicates_counter_matches_log(node):
    node.offline_send(8)
    pub = published(node.cmd("NET UP", 8))
    assert node.status()["duplicates"] == len(pub) - len(set(pub))


def test_rec5d_stress_counters_connected(node):
    out = node.cmd("STRESS 100", 6)
    assert len(published(out)) == 100
    assert node.status()["sent"] == 100


# ---------------------------------------------------------------- REC-6
@pytest.mark.parametrize("arg", ["-5", "1.5", "abc", "10 20"])
def test_rec6a_stress_invalid_rejected(node, arg):
    out = node.cmd(f"STRESS {arg}", 3)
    assert any("ERROR" in l for _, l in out), "no [CLI] ERROR"
    assert node.status()["sent"] == 0


@pytest.mark.parametrize("arg", ["0", "501"])
def test_rec6b_stress_out_of_range_reported(node, arg):
    out = node.cmd(f"STRESS {arg}", 3)
    assert any("ERROR" in l for _, l in out), "silently clamped (assumption: must report)"


def test_rec6c_net_down_idempotent(node):
    node.raw(b"NET DOWN\nNET DOWN\n"); out = node.pump(1.5)
    n = sum(1 for _, l in out if "state=DISCONNECTED" in l)
    assert n == 1, f"{n} DISCONNECTED transitions for 2 NET DOWN"


def test_rec6d_net_up_when_connected_is_silent(node):
    out = node.cmd("NET UP", 2)
    assert not any("network restored" in l for _, l in out), "network restored logged while connected"
