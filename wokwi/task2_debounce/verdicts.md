| ID | Scenario | RAW (final) | Logical | Actions | | Expected | Verdict |
|---|---|---:|---:|---:|---|---|---|
| BT-01 | bt01_pulse_1ms | 2 | 0 | 0 | - | eq 0 | PASS |
| BT-02 | bt02_pulse_5ms | n/a | 0 | 0 | - | eq 0 | PASS |
| BT-03 | bt03_pulse_10ms | 2 | 1 | 1 | - | eq 0 | FAIL |
| BT-04 | bt04_pulse_20ms | 2 | 1 | 1 | - | eq 0 | FAIL |
| BT-05 | bt05_pulse_29ms | 2 | 1 | 1 | - | eq 0 | FAIL |
| BT-06 | bt06_pulse_30ms | 2 | 1 | 1 | - | review | REVIEW |
| BT-07 | bt07_pulse_31ms | 2 | 1 | 1 | - | eq 1 | PASS |
| BT-08 | bt08_pulse_50ms | 2 | 1 | 1 | - | eq 1 | PASS |
| TC-01 | tc01_normal_press | 169 | 1 | 1 | - | eq 1 | PASS |
| TC-02 | tc02_bounce | 128 | 1 | 1 | - | eq 1 | PASS |
| TC-03 | tc03_long_press | 37 | 1 | 1 | - | eq 1 | PASS |
| TC-04 | tc04_five_rapid_presses | 675 | 5 | 5 | - | eq 5 | PASS |
| TC-05 | tc05_noise_tap | 2 | 0 | 0 | - | eq 0 | PASS |
| TC-06 | tc06_noise_in_critical | 153 | 2 | 2 | - | eq 1 | FAIL |
| TC-06b | tc06b_noise_500us_in_critical | 83 | 1 | 1 | - | eq 1 | PASS |
| TC-07 | tc07_repeat_noise_2ms | 2 | 1 | 1 | - | eq 0 | FAIL (PASS 0/5) |
| TC-08 | tc08_release_edge | 154 | 1 | 1 | - | eq 1 | PASS |
| TC-09 | tc09_led_matches_event | 166 | 1 | 1 | - | eq 1 | PASS |
| TC-10 | tc10_ten_presses_1ps | 1213 | 10 | 10 | - | eq 10 | PASS |
| TC-11 | tc11_boot_idle | n/a | 0 | 0 | - | eq 0 | PASS |
| TC-12 | tc12_raw_since_previous | 436 | 3 | 3 | - | eq 3 | PASS |
| TC-13 | tc13_two_presses_200ms | 303 | 2 | 2 | - | eq 2 | PASS |
| TC-14 | tc14_gap_15ms | 162 | 2 | 2 | - | eq 1 | FAIL |
| TC-15 | tc15_fast_tap_10ms | 157 | 1 | 1 | - | review | REVIEW |
| TC-17 | tc17_hold_60s | 158 | 1 | 1 | - | eq 1 | PASS |
| TC-18 | tc18_twenty_noise_taps | 40 | 0 | 0 | - | eq 0 | PASS |
| TC-19 | tc19_noise_while_held | 106 | 1 | 1 | - | eq 1 | PASS |
| TC-20 | tc20_noise_before_press | 179 | 1 | 1 | - | eq 1 | PASS |
| TC-21 | tc21_noise_after_release | 61 | 1 | 1 | - | eq 1 | PASS |
| TC-22 | tc22_btn_and_noise_together | 96 | 1 | 1 | - | eq 1 | PASS |
| TC-23 | tc23_noise_during_action | 139 | 2 | 2 | - | eq 1 | FAIL |
| TC-24 | tc24_mash_10s | 1195 | 25 | 25 | - | le 60 | INVALID (timed out / killed) |
| TC-26a | tc26a_soak_20_presses | 2704 | 20 | 20 | - | eq 20 | PASS |
| TC-26b | tc26b_soak_20_presses | 2679 | 20 | 20 | - | eq 20 | PASS |
| TC-26c | tc26c_soak_20_presses | 2510 | 20 | 20 | - | eq 20 | PASS |
| TC-26d | tc26d_soak_20_presses | 2494 | 20 | 20 | - | eq 20 | PASS |
| TC-26e | tc26e_soak_20_presses | 2349 | 20 | 20 | - | eq 20 | PASS |
| TC-27 | tc27_log_interleave | 1414 | 12 | 12 | - | eq 12 | PASS |
