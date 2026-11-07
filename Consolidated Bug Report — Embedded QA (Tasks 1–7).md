# Consolidated Bug Report — Embedded QA (Tasks 1–7)

Prepared by Serhii, QA Embedded Engineer · Consolidated 30 October 2026 · Source: Embedded\_QA archive (Tasks 1–7)

## 1. Executive summary

Seven projects were tested black-box on simulated hardware (Wokwi). **36 defects** were logged in total, and every project ended with a FAIL / not-ready-for-release verdict. Severity labels below are kept exactly as each project reported them, because the projects used different scales (Blocker/Major/Minor, Critical/Major, High/Medium, and so on). Task-specific IDs are kept, with a consolidated ID (T1-01 … T7-07) added for cross-reference.

| Task | Project / device | Test date | Defects | Severity as reported | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Smart Gate Controller (Arduino Uno, Wokwi 3.7.0) | 2026-09-23 | 12 | 5 Blocker, 3 Major, 3 Minor, 1 “Intermittent” (see note) | FAIL, not ready to release |
| 2 | Button Debounce (ESP32) | 2026-10-01 | 1 | 1 Major | FAIL (AC4, AC5) |
| 3 | UART CLI Homework Device v2.0 (ESP32) | 2026-10-03 | 5 | 1 Critical, 4 Major | Not ready for release |
| 4 | I2C trace, ESP32 + MPU-6050 | 2026-10-09 | 2 | 2 High | FAIL |
| 5 | Recovery / Fault Injection, build “homework\_buggy” (ESP32) | 2026-10-14 | 5 | 3 Major (High), 2 Medium | NO-GO |
| 6 | Python/Pytest, JSON serial protocol, firmware BUGGY (ESP32) | not stated | 4 | 2 High, 1 Medium, 1 Low/Medium | Not acceptable until BUG-1…3 are fixed |
| 7 | IoT Network / Memory Stability, “homework\_buggy” (ESP32 + DHT22) | 2026-10-24 | 7 | 3 Critical, 2 Major, 1 Minor, 1 Trivial | FAIL |

**Environment.** Task 1: macOS 12, MacBook Pro mid-2015, Chrome 150, VS Code 1.136, PlatformIO IDE 3.3.2, Wokwi 3.7.0. Tasks 2–7: Wokwi CLI v0.27.1 (Tasks 5–7 with Python 3.9.12, pytest 8.4.2, pyserial over RFC2217).

## 2. Highest-risk defects (release blockers)

1. **T1-09 / T1-06 — both gate relays can be energized together on a direction reversal** (R8, R4). Safety-relevant: can damage the motor or H-bridge.
2. **T1-02, T1-03, T1-11 — the gate never reaches OPEN and cannot be recovered by RESET** (power-cycle only).
3. **T3-05 — any UART input longer than 40 characters crashes and reboots the device** (52 faults in logs, 8 of 13 failed tests).
4. **T7-03, T7-04, T7-05 — the buffer overflows silently, the heap leaks 80 B per message, and the flush after overflow loses and multiplies messages.**
5. **T5-01 — an interrupted save changes the persistent counter by +100 and nothing detects the corruption** (R6).
6. **T6-02 and T6-03 — RESET reports OK but does not reset LED/PWM, and GET TEMP returns invalid JSON.**
7. **T4-01 — the device goes permanently silent on the I2C bus after the first NACK.**

## 3. Defects by project

### Task 1 — Smart Gate Controller (12 defects)

**T1-01 (#1) Movement timeout does not move OPENING → ERROR** · R9 · Major · 5/5 Steps: from CLOSED send O; do not reach the limit switch; wait more than 10 s. Expected: “ERROR: movement timeout”, state OPENING → ERROR. Actual: stays OPENING. Note: the same timeout works in CLOSING, so R9 is implemented asymmetrically.

*Evidence* (Task 1 serial output as recorded in Bug\_Report\_Serhii\_Shtelmakh.xlsx, TC-01, TC-08; the archive holds no raw serial file for this task):

```text
COMMAND: O
STATE: CLOSED -> OPENING
(more than 10 s, no limit switch)  -> no "ERROR: movement timeout", state stays OPENING
--- same test while CLOSING (TC-08) ---
ERROR: movement timeout
STATE: CLOSING -> ERROR
```

**T1-02 (#2) OPEN limit does not move the gate to OPEN** · R6 · Blocker · 5/5 Steps: in OPENING activate LIMIT\_OPEN. Expected: state OPEN, OPEN relay OFF. Actual: “OPEN LIMIT DETECTED” repeated (155 lines), OPEN relay stays ON, no state change. Blocks TC-03.

*Evidence* (xlsx, TC-02):

```text
Message: OPEN LIMIT DETECTED   (repeated, 155 lines)
State = OPEN LIMIT DETECTED
OPEN relay = ON | CLOSE relay = OFF | OPEN LED = ON
```

**T1-03 (#3) OPEN state unreachable, so R15 cannot be verified** · R15 · Blocker · 5/5 Direct consequence of T1-02: both relays cannot be checked as OFF in OPEN because OPEN is never entered.

*Evidence* (xlsx, Bug #3, TC-02): same output as T1-02; TC-03 (close from OPEN) is BLOCKED by TC-02, so R15 could not be checked in OPEN.

**T1-04 (#4) OPEN LED stays ON after STOP from OPENING** · R14 · Minor · 5/5 Expected OPEN LED OFF in STOPPED. Actual: state and relays correct, LED stays ON.

*Evidence* (xlsx, TC-05):

```text
STATE: OPENING -> STOPPED
OPEN relay = OFF | CLOSE relay = OFF | OPEN LED = ON   (expected OPEN LED = OFF, R14)
```

**T1-05 (#5) OPEN LED stays ON after STOP from CLOSING** · R14 · Minor · 5/5 Same as T1-04, starting from CLOSING.

*Evidence* (xlsx, TC-06):

```text
STATE: CLOSING -> STOPPED
OPEN relay = OFF | CLOSE relay = OFF | OPEN LED = ON   (expected OPEN LED = OFF, R14)
```

**T1-06 (#6) Opposite command reverses direction with no safe stop** · R4 · Blocker · 5/5 Steps: while CLOSING send O (and repeat from OPENING with C). Expected: CLOSING → STOPPED → OPENING. Actual: direct CLOSING → OPENING (or OPENING → CLOSING).

*Evidence* (xlsx, Bug #6):

```text
observed: CLOSING -> OPENING        (and OPENING -> CLOSING)
expected: CLOSING -> STOPPED -> OPENING
```

**T1-07 (#7) Both limit switches active during OPENING gives a warning loop, not ERROR** · R10 · logged severity “Intermittent” · 5/5 Actual: “WARNING: both limit switches active” plus an endless “OPEN LIMIT DETECTED” loop; ERROR is never entered. Note: “Intermittent” is a reproducibility label, not a severity, and the bug reproduces 5/5. It needs re-rating (T1-11 shows the consequence is unrecoverable).

*Evidence* (xlsx, Bug #7):

```text
WARNING: both limit switches active
OPEN LIMIT DETECTED
WARNING: both limit switches active
OPEN LIMIT DETECTED     ... endless loop, no ERROR state
```

**T1-08 (#8) Invalid command in CLOSED is silently dropped** · R13 · Minor · 5/5 C sent in CLOSED (also O in OPEN): no motion, but no diagnostic is printed as R13 requires.

*Evidence* (xlsx, Bug #8): State = CLOSED and relays OFF after C; the Serial Monitor shows no diagnostic line at all (the same silent drop for O while in OPEN).

**T1-09 (#9) Both relays briefly active during a CLOSING → OPENING reversal** · R8 · Blocker · 4/5 (timing-dependent) Because STOPPED is skipped (T1-06), relayOpen (pin 8) goes HIGH one control cycle before relayClose (pin 9) goes LOW. Safety-relevant (motor/H-bridge damage).

*Evidence* (xlsx, Bug #9, pin probe on consecutive control-loop cycles after O sent in CLOSING):

```text
(recorded observation, not a raw log)
relayOpen (pin 8) driven HIGH one control cycle before relayClose (pin 9) driven LOW
-> both relays energized for one cycle
```

**T1-10 (#10) RESET outside ERROR changes state** · R12 · Major · 5/5 Expected: no-op. Actual: always reports CLOSED (seen from OPEN, STOPPED, CLOSED); from OPEN the OPEN LED also stays ON.

*Evidence* (xlsx, Bug #10): RESET sent from OPEN, STOPPED and CLOSED, each answered with State = CLOSED; from OPEN the OPEN LED stays ON.

**T1-11 (#11) RESET cannot clear the limit-switch loop** · R10/R11 · Blocker · 5/5 After T1-07, RESET has no effect, messages keep printing, OPEN relay stays ON; only restarting the simulation clears it.

*Evidence* (xlsx, Bug #11): after RESET the "OPEN LIMIT DETECTED" / "WARNING" messages keep printing and the OPEN relay stays ON; only a power-cycle of the Wokwi simulation cleared it.

**T1-12 (#12) Zero debounce: one press produces multiple commands** · R16 · Major · 5/5 (key held 100 ms or longer) diagram.json sets bounce “0” on all three buttons; holding a key about 150 ms logged 3–6 “COMMAND: O” lines (same for C and S). The bounce attribute is simulation-level, so field impact is likely but unproven.

*Evidence* (xlsx, Bug #12; diagram.json):

```text
btnOpen, btnClose, btnStop: "bounce": "0"
key "o" held ~150 ms -> COMMAND: O printed 3-6 times (expected once)
```

### Task 2 — Button Debounce (1 defect)

**T2-01 (BUG-001) NOISE pulses of 2 ms or longer are accepted as button presses** · AC4, AC5 · Major / High · 5/5 Steps: without touching BUTTON, hold NOISE low for 2 ms and release; watch the Serial Logger for 3.5 s; repeat with 0.5, 1, 10, 20, 29, 30 ms. Expected: pulses below the debounce threshold (assumed about 30 ms) give 0 events and 0 actions. Actual: from 2 ms up, “LOGICAL EVENT #1”, “ACTION executed ONCE”, RAW 2 / Logical 1 / Actions 1. 0.5 ms and 1 ms are ignored correctly. The effective threshold is 1–2 ms. The same cause explains TC-06 (5 ms noise) and TC-23 (10 ms noise) adding a second event during the critical operation, and TC-14 (15 ms gap between two presses gives 2 events). Affected: TC-07 (5/5), BT-03…BT-06, TC-14, TC-06, TC-23. Open question: the 30 ms threshold is an assumption. If about 1 ms is the intended design, this is a requirements gap, not a firmware defect.

*Evidence* (Task2/results\_v2/\*.log, Serial Logger summary lines; verdicts.md):

```text
bt01_pulse_1ms   : [LOGGER] RAW interrupts: 2 | Logical events: 0 | Actions: 0   (ignored, correct)
bt03_pulse_10ms  : LOGICAL EVENT #1 / ACTIONS total: 1 / ACTION executed ONCE / Button RELEASE accepted
                   [LOGGER] RAW interrupts: 2 | Logical events: 1 | Actions: 1   (expected 0/0)
tc07_..._run1..5 : RAW 2 | Logical events: 1 | Actions: 1   (5 of 5 runs, 2 ms noise)
tc06_noise_in_critical   : RAW 153 | Logical events: 2 | Actions: 2   (expected 1)
tc14_gap_15ms            : RAW 162 | Logical events: 2 | Actions: 2   (expected 1)
tc23_noise_during_action : RAW 139 | Logical events: 2 | Actions: 2   (expected 1)
```

verdicts.md: BT-03, BT-04, BT-05 FAIL; TC-07 FAIL (PASS 0/5); TC-06, TC-14, TC-23 FAIL; BT-01 PASS; TC-06b (500 µs) PASS. Run header in each log: Wokwi CLI v0.27.1, scenarios\_v2/\*.test.yaml.

### Task 3 — UART CLI Homework Device v2.0 (5 defects)

**T3-01 (BUG-01) set speed 256 is accepted and silently set to 255** · REQ-03 · Major / Medium · 5/5 Steps: set speed 77, then set speed 256. Expected: ERROR, speed stays 77. Actual: “OK: speed=255”. Values -1, 999 and 100000 are rejected correctly.

*Evidence* (logs/TC-10.log, scenario TC-10.yaml):

```text
> OK: speed=77
> OK: speed=255
```

**T3-02 (BUG-02) set timeout 0 is accepted** · REQ-05 · Major / Medium · 5/5 (22/22 attempts) Steps: set timeout 33, then set timeout 0. Expected: ERROR, timeout stays 33. Actual: “OK: timeout=0”. 61 and -5 are rejected correctly.

*Evidence* (logs/TC-17.log):

```text
> OK: timeout=33
> OK: timeout=0
```

**T3-03 (BUG-03) status is not case-insensitive** · REQ-06 · Major / Medium · 5/5 Steps: send HELP, then Status. Expected: both return ERROR. Actual: HELP gives “ERROR: unknown command”, but Status executes and prints the full status. LED ON and Set speed 10 variants were not reached because the scenario stopped.

*Evidence* (logs/TC-21.log):

```text
> OK: speed=77
> ERROR: unknown command      <- HELP
> SPEED=77                    <- Status executed
TIMEOUT=10
LED=OFF
CONFIG=DIRTY
```

**T3-04 (BUG-04) Special-character-only input is treated as a valid command** · REQ-08 · Major / Medium · 5/5 (25/25 attempts) Inputs such as !@#$%^&\*(), ;;;; and \~\`|<>? each return “OK” instead of “ERROR: unknown command”. Configuration is unchanged afterwards.

*Evidence* (logs/TC-24.log; also TC-35):

```text
> OK
> 
```

**T3-05 (BUG-05) Input longer than 40 characters crashes and reboots the device** · REQ-11, 12, 14, 16 · Critical / High · 5/5 (26/26 attempts) Steps: open the UART console, send 41 characters (for example 41 × “A”). Expected: “ERROR: command too long”, device keeps running. Actual: “\*\*\* SYSTEM FAULT \*\*\* Reason: input line boundary failure”, SW\_CPU\_RESET, reboot, then “ERROR: empty command”. 40 characters are fine (TC-26); longer input gives more reboots (41 chars: 1, 200: 4, 1000: 11). Independent of prior commands (52 faults, same cause). Whether unsaved DIRTY config is lost on reboot was not checked.

*Evidence* (logs/TC-27.log, 41-character line):

```text
> 
*** SYSTEM FAULT ***
Reason: input line boundary failure
rst:0xc (SW_CPU_RESET)
Rebooting...
 UART CLI HOMEWORK DEVICE v2.0
 READY
> ERROR: empty command
```

Same fault in TC-28 (4 reboots), TC-29 (11), TC-30, TC-31, TC-33, TC-35 (20) and TC-36 (10); all runs: wokwi-cli v0.27.1, firmware v2.0, 2026-10-03; results.csv exit code 42 = failed step.

### Task 4 — I2C trace, ESP32 + MPU-6050 (2 defects)

**T4-01 (BUG-01) After the first NACK the device stops all I2C activity** · implicit requirement (none provided) · High · 1/1 capture Steps: capture SDA/SCL; wait for at least 5 normal cycles; switch FAULT on; capture at least 30 s. Expected: continued polling or retries, and some way of reporting the loss. Actual: one NACK at 609.122546 s on 0xD2 (0x69 W), a STOP 14.9 µs later, then no bus activity until 642.210 s (33.09 s, about 33 missed 1.001 s cycles). The bus is released correctly (SDA and SCL high).

*Evidence* (Task4/home\_work4.sr logic-analyzer capture; Protocol Analysis Sheet.xlsx, tabs Timing and Trace Summary; 610 decoded transactions, 642.21 s):

```text
  0.513591 s  init: write 0x68, reg 0x6B, data 0x00 (ACK)
  608.121456  START of cycle #608 (last normal read: 0x68 W, 0x41, Sr, 0x68 R, data 0xEF 0x5C)
  608.121772  last slave ACK (0xD1 = 0x68 R)
  608.121878  last master ACK (after 0xEF)
  609.122456  START, address 0x69 W (0xD2), 1001.000 ms after previous cycle
  609.122546  slave NACK (9th clock)         START->NACK 89.4 us
  609.122561  STOP                            NACK->STOP  14.9 us
  642.210284  end of capture, SDA and SCL both high  -> 33.09 s silence, ~33 cycles missed
```

**T4-02 (BUG-02) No recovery or reboot visible after the NACK** · implicit requirement · High (proposed) · 1/1 capture, retest needed No 0x68 traffic, no 0x6B re-initialization, no reboot pattern in the window. Caveat: the trace does not show when, or whether, FAULT was switched back OFF, so this is partly a missing test (FAULT off at a known time). It may be merged with T4-01 after the retest.

*Evidence* (same capture): no transaction to 0x68, no 0x6B write and no reboot pattern between 609.122561 s and 642.210284 s. The trace does not show when FAULT was switched off, so recovery is not proven either way (QA Conclusion PDF, section 6).

### Task 5 — Recovery / Fault Injection, build “homework\_buggy” (5 defects)

**T5-01 (BUG-01) Interrupted save leaves the counter at old+100, corruption undetected** · R6 · Major (High) · 5/5 Steps: send status and note the counter; send powerloss; wait for the boot banner; send status. Expected: old or new valid value (old+1), corruption logged. Actual: counter grows by exactly 100 each time (730 → 831, 933, 1034, 1134, 1234); no corruption message at start-up.

*Evidence* (Task5/serial\_20261014\_152215.log, ELF SHA256 1e9f6d28d20fb872):

```text
...216.244  "reset_reason":"INT_WDT","relay":false,"counter":8,...
...216.664  [FAULT] power loss DURING save
...217.956  "reset_reason":"SOFTWARE_RESET","relay":false,"counter":108,...
```

Sheet evidence, counter before > after: 730 > 831, 833 > 933, 934 > 1034 > 1134 > 1234 (5 of 5 powerloss events).

**T5-02 (BUG-02) Wake-up time ignores the requested sleep duration** · R4 · Major (High) · 5/5 sleep N wakes after about 0.4–0.7 s regardless of N: 0.41 s (3), 0.59 s (5), 0.70 s (10), 0.71 s (20). Expected N ±15%. Reset reason DEEPSLEEP\_RESET, wake cause 4 (timer). Measured on the simulator clock; confirm against firmware uptime.

*Evidence* (same serial log, timestamps in epoch seconds):

```text
...137.590  [STORE] saved  [STATE] SLEEP timer=3 s
...137.956  rst:0x5 (DEEPSLEEP_RESET)          -> about 0.4 s
...139.768  [STATE] SLEEP timer=5 s
...140.310  boot:0x13 (SPI_FAST_FLASH_BOOT)    -> about 0.5 s
[BOOT] reset_reason=DEEP_SLEEP  [WAKE] cause=4
```

pytest: test\_wake\_time\_within\_tolerance\[3|5|10|20\] and test\_repeated\_sleep\_cycles\_and\_heap fail (0.41 / 0.59 / 0.70 / 0.71 s).

**T5-03 (BUG-03) Watchdog reset takes about 14.6 s instead of 5 s** · R5 · Major (High) · 1 timed measurement, consistent with 10 logged hang cycles hang → reboot after 14.59 s, reset reason INT\_WDT (TG1WDT\_SYS\_RESET); firmware reports timeout=4000 ms. The device recovers normally. Confirm timing against firmware time.

*Evidence* (same serial log; pytest test\_wdt\_fires\_in\_time = 14.59 s):

```text
E (21619) task_wdt: Task watchdog got triggered. The following tasks did not reset the watchdog in time:
E (21619) task_wdt:  - loopTask (CPU 1)
E (21619) task_wdt: Aborting.
rst:0x8 (TG1WDT_SYS_RESET)
[BOOT] reset_reason=INT_WDT
[WDT] enabled timeout=4000 ms
```

task\_wdt triggers logged at uptime 21735, 14974, 24310, 15804, 24711, 16317, 18639, 19717 ms.

**T5-04 (BUG-04) sleep accepts invalid arguments and silently substitutes values** · R4 and negative-input handling · Medium · 18/18 Empty → 5 s, 0 and text → 1 s, 3.5.1 → 3 s, negative or huge → 60 s; state is saved and the device sleeps instead of returning an error (unknown commands are rejected correctly, so the error path exists).

*Evidence* (pytest test\_invalid\_sleep\_args\_after\_recovery, 18 cases, all failed; sheet log excerpt):

```text
sleep (empty) -> [STATE] SLEEP timer=5 s
sleep 0 / abc -> [STATE] SLEEP timer=1 s
sleep 3.5.1   -> [STATE] SLEEP timer=3 s
sleep -5 / sleep 99999999999 -> [STATE] SLEEP timer=60 s
(no "[CLI] ERROR"; [STORE] saved is printed)
```

**T5-05 (BUG-05) 60 s sleep ends with an INT\_WDT reset instead of a timer wake-up** · R4, R5 · Medium · 6/6 sleep -5 or sleep 99999999999 (both become timer=60 s) → TG1WDT\_SYS\_RESET within the 3 s observation window. Possibly the same root cause as T5-02 and T5-03.

*Evidence* (serial log, lines at ...293.507, ...298.272, ...303.489 and the matching resets):

```text
[STATE] SLEEP timer=60 s
rst:0x8 (TG1WDT_SYS_RESET)
reset_reason=INT_WDT          (6 of 6 cases; timer=1/3/5 s end in DEEPSLEEP_RESET)
```

### Task 6 — Python/Pytest, JSON serial protocol, firmware BUGGY (4 defects)

**T6-01 (BUG-1) SET PWM 100 returns INVALID\_VALUE** · Req. 5 · Medium · 5/5 Expected {"status":"OK","pwm":100}. Actual {"status":"ERROR","code":"INVALID\_VALUE"}; 99 is OK, 101 is INVALID\_VALUE (upper boundary, looks like < instead of <=).

*Evidence* (Task6/manual\_check\_1.log; pytest test\_pwm\_valid\_boundaries\[100\]: assert 'ERROR' == 'OK', tests/test\_boundaries.py:6):

```text
19:23:45 TX SET PWM 99
19:23:45 RX {"status":"OK","pwm":99}   (0.27s)
19:23:45 TX SET PWM 100
19:23:45 RX {"status":"ERROR","code":"INVALID_VALUE"}   (0.32s)
```

Same result in manual\_check.log (19:04:42) and manual\_check\_476e74.log (12:34:18).

**T6-02 (BUG-2) RESET answers OK but does not turn the LED off or clear PWM** · Req. 7 · High · 5/5 per run Steps: SET LED ON, SET PWM 50, RESET, STATUS. Expected led=false, pwm=0. Actual: {"led":true,"pwm":127}; after SET LED ON then RESET, pwm stays 255. The safe-state command reports success but does nothing.

*Evidence* (manual\_check\_1.log; pytest test\_reset\_clears\_pwm\[1,50,99\]: 2 == 0, 127 == 0, 252 == 0; test\_reset\_turns\_led\_off; test\_reset\_restores\_safe\_state: 255 == 0):

```text
19:23:55 TX SET LED ON
19:23:55 RX {"status":"OK","led":true}   (0.35s)
19:23:55 TX SET PWM 50
19:23:56 RX {"status":"OK","pwm":50}   (0.24s)
19:23:56 TX RESET
19:23:57 RX {"status":"OK","reset":true}   (0.30s)
19:23:57 TX STATUS
19:23:57 RX {"status":"OK","led":true,"pwm":127,"heap":349852}   (0.31s)
```

**T6-03 (BUG-3) GET TEMP returns invalid JSON** · Req. 3 · High · 100% Actual {"status":"OK","temperature":24.5 with no closing brace (the firmware format string is missing it); json.loads fails. All 6 manual requests and 4 tests affected.

*Evidence* (manual\_check\_1.log; pytest test\_temperature\_is\_valid\_json: "Invalid JSON from device"; json.loads: Expecting ',' delimiter, line 1 column 34):

```text
19:23:41 TX GET TEMP
19:23:41 RX {"status":"OK","temperature":24.5   (0.30s)
19:23:42 RX {"status":"OK","temperature":24.5   (0.19s)
19:23:42 RX {"status":"OK","temperature":24.5   (0.19s)
```

**T6-04 (BUG-4) PING blocks command processing for about 1.3 s** · Req. 1, 9 (no latency limit defined) · Low / Medium · 100% PING answers in 1.31–1.40 s; a STATUS sent right after it answers in 1.46 s instead of about 0.2 s (median PING 5.7× STATUS). Severity depends on the response-time limit, which the requirements do not define.

*Evidence* (manual\_check\_1.log, PING; pytest test\_status\_right\_after\_ping\_is\_not\_blocked and test\_ping\_is\_not\_an\_outlier\_vs\_status):

```text
19:23:31 TX PING
19:23:32 RX {"status":"OK","command":"PING"}   (1.33s)
19:23:34 RX {"status":"OK","command":"PING"}   (1.39s)
19:23:35 RX {"status":"OK","command":"PING"}   (1.32s)
pytest: STATUS answered after 1.46s (PING after 1.35s)
pytest: PING median 1.36s is 5.7x STATUS median 0.24s
```

Control test\_two\_status\_commands\_in\_one\_write\_are\_fast passes (both answers under 1.0 s).

### Task 7 — IoT Network / Memory Stability (7 defects)

**T7-01 (BUG-01) Reconnect storm: about 19 retries per second, fixed 50 ms backoff** · R2 · Major / Medium · 5/5 runs Steps: NET DOWN; observe 20 s. Expected: growing backoff, no more than 12 retries in 20 s. Actual: backoff 500 ms once, then 50 ms in 2,059 of 2,071 retry lines (391 retries in 20 s). The node does recover about 3 ms after NET UP.

*Evidence* (Task7/device\_monitor-log/device-monitor-261024-174403.log, run C; run A excerpt from the sheet):

```text
17:44:20.504 > [NET] retry=1 backoff_ms=500
17:44:20.966 > [NET] retry=2 backoff_ms=50
17:44:21.016 > [NET] retry=3 backoff_ms=50
17:44:52.671 > {"net":"BACKOFF","broker":false,"buffer":0,...,"reconnect_attempts":233,"heap":350868}
run A: 17:20:00.890 retry=84 -> 17:20:04.005 retry=144   (60 retries in 3.1 s)
```

TC-03: 391 retries in 20 s; backoff\_ms=50 in 2,059 of 2,071 retry lines (run B).

**T7-02 (BUG-02) Every buffered message is published twice after NET UP** · R6 (also R5, R8) · Major / Medium · 6/6 runs Steps: NET DOWN, SEND ×5 (or ×8), NET UP. Expected: each ID once, duplicates=0. Actual: every ID published twice (12 messages → 24 publishes); in TC-28 all 20 flushes duplicated (sent=120, dup=60). The duplicates counter also disagrees with the log (12 vs 16 real repeats).

*Evidence* (run C log, 17:46:01; flush of the 12-message case, first six publish lines):

```text
17:45:57.029 > [BUFFER] queued id=19 count=9/8
17:46:01.364 > [BUFFER] flush_start count=12
17:46:01.364 > [MQTT] publish id=19 temp=24.5
17:46:01.383 > [MQTT] publish id=19 temp=24.5
17:46:01.383 > [MQTT] publish id=20 temp=24.5
17:46:01.383 > [MQTT] publish id=20 temp=24.5
```

TC-28 (run F, device-monitor-261026-120544.log), last STATUS line: {"net":"CONNECTED","buffer":0,"sent":120,"dropped":0,"duplicates":60,"reconnect\_attempts":1046,"heap":345804}.

**T7-03 (BUG-03) Buffer grows past capacity 8; DROP\_OLDEST is logged but nothing is dropped** · R4 · Critical / High · 4/4 runs Steps: NET DOWN, SEND ×12. Expected: buffer=8, dropped=4. Actual: buffer=12, dropped=0 (9 SEND gives 9; STRESS 100 offline gives 100). Exactly 8 is handled correctly.

*Evidence* (run C log):

```text
17:45:57.028 > [BUFFER] overflow policy=DROP_OLDEST dropped_total=0
17:45:57.029 > [BUFFER] queued id=19 count=9/8
17:49:35.239 > {"net":"BACKOFF","broker":false,"buffer":10,"capacity":8,"sent":0,"dropped":0,"duplicates":0,"reconnect_attempts":21,"heap":256120}
```

Sheet (Fault Log, run B): SEND x12 -> buffer=12 (cap 8), dropped=0; SEND x9 -> buffer=9; STRESS 100 offline -> buffer=100.

**T7-04 (BUG-04) Memory leak: free heap drops 80 B per message and never recovers** · R7 · Critical / High · 5/5 runs Steps: RESET STATS; STRESS 100 ×10. Expected: loss under 5%. Actual: 344,924 → 264,920 B (−80,004 B, −23.2%); TC-28: −240 B per reconnect cycle (−5,064 B over 20 cycles). Projected exhaustion after about 4,300 messages.

*Evidence* (run C log, 10 x STRESS 100; sheet Memory Stability Log):

```text
17:47:42.980 > [STRESS] start count=100 heap=344924
17:47:43.228 > [STRESS] end heap=336924
17:47:50.983 > [STRESS] start count=100 heap=336924
17:47:51.225 > [STRESS] end heap=328932
17:47:58.585 > [STRESS] start count=100 heap=328932
17:47:58.838 > [STRESS] end heap=320920
```

Iteration 10: heap 264,920 B (-80,004 B, -23.2%). Run A: STRESS 500 start heap=256040, end heap=216040.

**T7-05 (BUG-05) Flush after overflow loses the oldest messages and repeats others 2–4 times** · R4, R5, R6 · Critical / High · 4/4 runs Steps: NET DOWN, SEND ×12, NET UP. Expected: 8 newest IDs once each, oldest first. Actual: 24 publishes, IDs 19–22 four times, 15–18 twice, IDs 11–14 never published, order starts at 19. STRESS 100 offline: 92 messages lost silently.

*Evidence* (run C log; the Message ID table in the sheet lists IDs 13–22):

```text
17:46:01.364 > [BUFFER] flush_start count=12
17:46:01.364 > [MQTT] publish id=19 ... id=22   (each twice)
17:46:01.396 > [MQTT] publish id=15 ... id=18   (each twice)
17:46:01.413 > [MQTT] publish id=19 ... id=22   (each twice again)
17:46:01.430 > [BUFFER] flush_end count=0
```

IDs 11–14 are never published; 24 publishes for 8 distinct IDs; STATUS afterwards: sent=24, dropped=0, duplicates=12.

**T7-06 (BUG-06) Invalid STRESS arguments run silently as count=1** · R2, R8 · Minor / Low · 2 runs STRESS -5, 1.5, abc each run with count=1, no “\[CLI\] ERROR”. Related: STRESS 10 20 runs 10; STRESS 0 runs 1; STRESS 501 and larger silently clamp to 500.

*Evidence* (device-monitor-261025-000245.log, run D, STRESS -5):

```text
00:06:13.228 > [STRESS] start count=1 heap=347244
00:06:13.231 > [MQTT] publish id=43 temp=24.5
00:06:13.231 > [STRESS] end heap=347164
(no [CLI] ERROR line)
```

Same behaviour for 1.5 (00:06:23.426) and abc (00:06:33.611); STRESS 10 20 (00:06:43.885) ran count=10; 99999999999 (00:06:53.936) ran 500.

**T7-07 (BUG-07) Fault commands are not idempotent** · R1, R2, R8 · Trivial / Low · 2 runs A second NET DOWN re-enters DISCONNECTED and increments retry; NET UP while CONNECTED logs “\[FAULT\] network restored” with no state change.

*Evidence* (run D log):

```text
00:04:47.531 > [NET] state=DISCONNECTED
00:04:47.532 > [NET] state=BACKOFF
00:04:47.534 > [NET] retry=64 backoff_ms=500
00:04:47.534 > [NET] state=DISCONNECTED     <- second NET DOWN
00:04:47.534 > [NET] state=BACKOFF
00:04:47.534 > [NET] retry=65 backoff_ms=50
00:04:58.724 > [FAULT] network restored    <- NET UP while already CONNECTED
```

## 4. Open questions and items not counted as defects

- **Task 1:** severity of T1-07 is mislabelled (“Intermittent”) and the buzzer on timeout is not in the requirements (raised as a requirements question).
- **Task 2:** TC-24 (watchdog timeout at 300 s), BT-02 (Wokwi connection drop) and TC-25 (manual, not run) are incomplete runs, not defects. No VCD was captured, so D0/D1/LED and pulse widths are unconfirmed. The debounce threshold needs confirming with the requirements owner.
- **Task 3:** after led on the config stays SAVED while set speed makes it DIRTY; the requirements do not say which is correct. Priorities are the tester’s proposal.
- **Task 4:** the device addressed 0x69 instead of 0x68 at the moment of failure. Confirm whether that is expected for the FAULT switch. A serial log or status GPIO is needed to see the firmware’s own error state.
- **Task 5:** relay state after a WDT reset is not verified, DHT22 failure and button bounce were not tested. powerloss is fault injection, not a real brown-out.
- **Task 6:** QUESTION-1 (STATUS shows pwm on a 0–255 scale while SET PWM uses 0–100) and QUESTION-2 (LED and PWM behave as one output) are requirement questions, not counted as bugs. One ERROR (test\_no\_response\_becomes\_timeout) was an environment/setup event.
- **Task 7:** TC-15 failed because of a test error, not a product defect. TC-27 (long outage) was skipped. Numeric thresholds (such as 12 retries per 20 s) are the tester’s assumptions.

## 5. Recommended next steps

1. Fix the release blockers in section 2 first, then re-run the affected suites for regression.
2. Get answers from the requirements owners on the open questions above (debounce threshold, PWM units, LED/PWM independence, PING latency limit, I2C recovery behaviour).
3. Repeat the timing-based findings (T5-02, T5-03) against firmware time or real hardware, and re-run T4 with FAULT switched off at a known moment.
