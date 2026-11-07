# Test Cases by Group

*System under test: ESP32 IoT Controller (Wokwi simulation). Source: homework assignment + device_requirements.md (R1–R7).*

Marker † = test needs helper commands (`relay on`, `save <value>`, `load`) that are not defined in the requirements; it is skipped if the firmware does not support them.

## Group 1. Sleep / Wake (ACTIVE → SLEEP → WAKE)

| ID | Title | Steps | Expected result | Req |
|---|---|---|---|---|
| TC-SLP-01 | Boot to ACTIVE | Start device, read boot log, send `status` | `state=ACTIVE`, reset reason printed | R1 |
| TC-SLP-02 | Sleep 5 s, wake-up accuracy | Send `sleep 5`, measure time until next boot banner | Wake-up in 5 s ±15% (4.25–5.75 s) | R4 |
| TC-SLP-03 | Wake-up accuracy for several values (parametrized) | `sleep N` for N = 3, 5, 10, 20 | Every wake-up within ±15% of N | R4 |
| TC-SLP-04 | Reset reason after wake | After TC-SLP-02 send `status` | Reset reason is DEEPSLEEP / timer wake, not POWERON/WDT | R1, R4 |
| TC-SLP-05 | Device operable after wake | After wake send `status` and `sleep 3` again | `state=ACTIVE`, CLI answers, second sleep cycle works | R4 |
| TC-SLP-06 | Repeated sleep cycles | Run 5 consecutive `sleep 3` cycles | No drift outside ±15%, no hang, heap does not shrink steadily (leak check) | R4, R7 |
| TC-SLP-07 | Persistent data after sleep† | `save 42`, `sleep 3`, after wake `load` | Value 42 is intact | R4 |
| TC-SLP-08 | Sensor after wake | After wake read `status` | Sensor status valid (DHT22 reads 24.5 °C / 45 %), no false error | R2, R4 |

## Group 2. Watchdog

| ID | Title | Steps | Expected result | Req |
|---|---|---|---|---|
| TC-WDT-01 | WDT fires on hang | Send `hang`, measure time to reboot | Reboot within 5 s (+ ~1 s boot margin) | R5 |
| TC-WDT-02 | Reset reason is WDT | After TC-WDT-01 send `status` | Reset reason identifies WDT | R5 |
| TC-WDT-03 | Device operable after WDT reset | `status`, `sleep 3` after recovery | `state=ACTIVE`, CLI responsive | R5 |
| TC-WDT-04 | Actuator OFF after emergency reset† | `relay on`, `hang`, wait reboot, `status` | `relay=OFF` | R5 |
| TC-WDT-05 | No boot loop | After recovery observe serial for 20 s | No additional reboot banners | R5 |
| TC-WDT-06 | Repeated hang/recovery | 3 × (`hang` → recovery → `status`) | Each cycle recovers in time, no degradation | R5 |
| TC-WDT-07 | Event counter / evidence | Compare `status` before and after | Reset reason and counters are observable and consistent | R7 |

## Group 3. Brown-out / power loss (interrupted save)

| ID | Title | Steps | Expected result | Req |
|---|---|---|---|---|
| TC-BRN-01 | Reboot after `powerloss` | Send `powerloss`, wait for reboot | Device reboots and returns to `ACTIVE` | R6 |
| TC-BRN-02 | Device operable after power loss | `status` after reboot | CLI responsive, sensor OK, relay OFF | R6 |
| TC-BRN-03 | State is old-valid or new-valid† | `save A`, `powerloss`, `load` | Value equals old (A) or fully new, never mixed | R6 |
| TC-BRN-04 | Corrupted state detection | If firmware reports state validity, check after `powerloss` | Corrupted state is flagged in log/status, not used silently | R6 |
| TC-BRN-05 | Repeated power loss | 5 × `powerloss` | Every recovery OK, no boot loop, state remains valid | R6 |
| TC-BRN-06 | Reset reason after power loss | `status` after reboot | Reset reason printed and does not claim DEEPSLEEP | R1, R6 |

## Group 4. Data persistence (EEPROM / RTC / NVS-Flash)

| ID | Title | Steps | Expected result | Req |
|---|---|---|---|---|
| TC-DAT-01 | NVS survives sleep† | `save X`, `sleep 3`, `load` | X intact | R4 |
| TC-DAT-02 | NVS survives WDT reset† | `save X`, `hang`, `load` | X intact | R5 |
| TC-DAT-03 | NVS survives interrupted save† | `save X`, `save Y` + `powerloss`, `load` | X or Y, fully valid | R6 |
| TC-DAT-04 | Event counter consistency | Read `events` before/after each recovery | Counter not corrupted (no garbage/negative values); documented behavior (kept or reset) | R7 |
| TC-DAT-05 | Data after many cycles† | Alternate sleep / WDT / powerloss 3 times | Saved value stays valid | R4–R6 |

## Group 5. Negative tests (invalid input after recovery)

| ID | Title | Input (sent right after recovery) | Expected result |
|---|---|---|---|
| TC-NEG-01 | Unknown command | `foobar` | Error message, no reboot, state ACTIVE |
| TC-NEG-02 | `sleep` without argument | `sleep` | Usage/error, no sleep |
| TC-NEG-03 | Negative value | `sleep -5` | Rejected, device stays ACTIVE |
| TC-NEG-04 | Zero value | `sleep 0` | Rejected or safe handling, no hang |
| TC-NEG-05 | Non-numeric value | `sleep abc` | Rejected, device stays ACTIVE |
| TC-NEG-06 | Huge value | `sleep 99999999999` | Rejected or clamped, no overflow/immediate wake |
| TC-NEG-07 | Empty line | (only LF) | Ignored, no crash |
| TC-NEG-08 | Very long line (1 KB) | `A` × 1024 | No crash/WDT reset, no buffer overflow |
| TC-NEG-09 | Binary garbage | random bytes `0x01–0xFF` | No crash, CLI recovers |
| TC-NEG-10 | Wrong case / extra spaces | `SLEEP  3`, ` status ` | Defined behavior (accepted or rejected), no crash |
| TC-NEG-11 | Invalid sensor data (R2) | Set DHT22 to unavailable in Wokwi, `status` | Sensor status = error, explicit log error, relay not driven by invalid data |
| TC-NEG-12 | Command flood | 50 × `status` in one burst | All answered or safely dropped, no WDT reset |

## Group 6. Parametrized tests

Implemented in code with `pytest.mark.parametrize`:

| ID | Parameters | Covers |
|---|---|---|
| TC-PAR-01 | `sleep N`, N ∈ {3, 5, 10, 20} | TC-SLP-03 |
| TC-PAR-02 | Number of recovery cycles ∈ {1, 3} × fault ∈ {hang, powerloss, sleep} | TC-WDT-06, TC-BRN-05, TC-SLP-06 |
| TC-PAR-03 | Invalid `sleep` args: empty, `-5`, `0`, `abc`, `99999999999`, `3.5.1` | TC-NEG-02…06 |
| TC-PAR-04 | Garbage payloads (unknown, empty, long, binary, symbols, spaces/case) | TC-NEG-01, 07…10 |
| TC-PAR-05 | Fault injection ∈ {hang, powerloss, sleep 3} × post-check ∈ {status OK, relay OFF, heap > 0} | TC-WDT-03/04, TC-BRN-02 |

## Group 7. Full suite run and logs

| ID | Title | Steps | Expected result |
|---|---|---|---|
| TC-RUN-01 | Run the whole suite locally | `pytest -v --junitxml=logs/report.xml --html=logs/report.html --self-contained-html` | All tests pass (skipped tests are listed with reason) |
| TC-RUN-02 | Collect logs | Attach `logs/report.xml`, `logs/report.html`, `logs/serial_*.log`, console output | Logs show every command and reboot banner |
| TC-RUN-03 | Repeatability | Run the suite 3 times | Same results, no flaky tests |
