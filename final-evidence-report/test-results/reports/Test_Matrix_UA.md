# Test Matrix — Крок 2 (Embedded QA, Tasks 1–7)

Матриця покриття ризиків тестами за вебінаром 8: **Ризик → Тип тестування → Докази тестування**, розширена до повної Test Matrix (Test Objective, Test Type, Test Level, Priority, Expected Result). Охоплює всі сім проєктів. Підготував Serhii, QA Embedded Engineer, 2026-11-01.

Пов'язані документи: [master-test-plan.md](../../master-test-plan.md) (розділ 7a) · [Risk_Matrix_UA.md](Risk_Matrix_UA.md) · [EVIDENCE_INDEX_UA.md](EVIDENCE_INDEX_UA.md) · [test_summary.md](test_summary.md)

## 1. Як читати матрицю

- **R1–R6** — критичні ризики з Кроку 1 вебінару: R1 неправильна команда керування, R2 датчик недоступний, R3 зависання прошивки, R4 втрата живлення під час збереження, R5 мережа недоступна, R6 деградація пам'яті.
- **QR-01…QR-12** — Quality Risks із Master Test Plan; **TM-01…TM-22** — тести; **T1-01…T7-07** — defects із Consolidated Bug Report.
- **Priority:** P1 = release blocker, має пройти; P2 = має пройти або мати waiver; P3 = до наступного milestone. Priority береться з Risk Matrix (Risk = Probability × Impact).
- Усі шляхи в таблицях відносні до `test-results/reports/`.

## 2. Матриця Кроку 2: Ризик → Тип тестування → Докази (за проєктами)

| R | Ризик | Task | Тип тестування | Докази тестування |
|---|---|---|---|---|
| R1 | Неправильна команда керування / некоректний вхід CLI | 3 UART CLI | Граничні значення / negative scenarios | Serial log + Wokwi CLI scenarios: [TC-10](../../logs/task3_uart_cli/TC-10.log), [TC-17](../../logs/task3_uart_cli/TC-17.log), [TC-21](../../logs/task3_uart_cli/TC-21.log), [TC-24](../../logs/task3_uart_cli/TC-24.log) |
| R1 | Неправильна команда керування (JSON-протокол) | 6 JSON protocol | Protocol, boundary / negative | Pytest + manual log: [pytest_output.txt](../../test-results/task6_protocol/pytest_output.txt), [manual_check_1.log](../../logs/task6_protocol/manual_check_1.log) |
| R1 | Неправильна команда керування воротами (реверс, RESET) | 1 Gate | Functional (safety), state machine | Serial log, стан relay pin: [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| R1 | Хибна команда через шум на кнопці | 2 Debounce | Boundary (sweep імпульсів), automation | Serial Logger (RAW / Logical events / Actions): [bt03](../../logs/task2_debounce/bt03_pulse_10ms_run1.log), [verdicts.md](../../test-results/task2_debounce/verdicts.md) |
| R2 | Датчик недоступний (NACK на I2C) | 4 I2C | Fault Injection (перемикач FAULT) | Trace I2C: [i2c_failure.sr](../../test-results/i2c_failure.sr), [Protocol Analysis Sheet](../../test-results/task4_i2c/Protocol%20Analysis%20Sheet.xlsx) |
| R2 | Збій DHT22 (Tasks 5, 7) | 5, 7 | Fault Injection | **Прогалина:** не тестувалося |
| R3 | Зависання прошивки (команда hang) | 5 Recovery | Recovery | Log перезапуску watchdog: [serial log Task 5](../../logs/task5_recovery/serial_20261014_152215.log), [pytest_log_task5.pdf](../../test-results/task5_recovery/pytest_log_task5.pdf) |
| R3 | Crash від надто довгого рядка | 3 UART CLI | Boundary / negative, robustness | [TC-27.log](../../logs/task3_uart_cli/TC-27.log) (SYSTEM FAULT, SW_CPU_RESET) |
| R3 | Watchdog на 300 с | 2 Debounce | Reliability | TC-24: INVALID (timed out), [verdicts.md](../../test-results/task2_debounce/verdicts.md) |
| R4 | Втрата живлення під час збереження | 5 Recovery | Reliability, persistence | Counter до / після: [serial log](../../logs/task5_recovery/serial_20261014_152215.log) (рядки 173–187) |
| R4 | Збереження конфігурації CONFIG SAVED / DIRTY | 3 UART CLI | Persistence | Частково: стан після crash не перевірявся |
| R5 | Збій мережі (NET DOWN / NET UP, backoff, buffer, flush) | 7 IoT network | Стрес-тест / recovery | Лог MQTT і message ID: [device-monitor-261024-174403.log](../../logs/task7_network_memory/device-monitor-261024-174403.log), [network_stress.csv](../../logs/network_stress.csv) |
| R6 | Деградація пам'яті (STRESS) | 7 IoT network | Memory stability | Heap-метрики: [task7_heap_trend.png](../../screenshots/task7_heap_trend.png), [network_stress.csv](../../logs/network_stress.csv) |
| R6 | Повторні sleep-цикли та heap | 5 Recovery | Reliability | [pytest_log_task5.pdf](../../test-results/task5_recovery/pytest_log_task5.pdf) (`test_repeated_sleep_cycles_and_heap`) |

**Покриття проєктів:** Task 1 → R1; Task 2 → R1, R3; Task 3 → R1, R3, R4; Task 4 → R2; Task 5 → R3, R4, R6; Task 6 → R1; Task 7 → R5, R6. Кожен із семи проєктів покриває щонайменше один критичний ризик.

## 3. Повна Test Matrix (22 тести)

Test Level: Component · Interface / protocol · System · Recovery / fault injection · Network (рівні з вебінару: component / interface checks, system black-box, fault injection, non-functional / reliability, automation / regression).

| Test ID | R · QR | Task | Test Objective | Test Type | Test Level | Priority | Expected Result | Evidence |
|---|---|---|---|---|---|---|---|---|
| TM-01 | R1 · QR-01 | 1 | Relay не вмикаються одночасно при реверсі (O під час CLOSING, C під час OPENING) | Functional (safety) | System | P1 | CLOSING → STOPPED → OPENING; relayOpen (pin 8) і relayClose (pin 9) ніколи не HIGH в одному циклі, 20 з 20 реверсів (R4, R8) | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| TM-02 | R1 · QR-02 | 1 | Movement timeout 10 с в обох напрямках | Functional | System | P1 | «ERROR: movement timeout», стан → ERROR, обидва relay OFF (R9) | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| TM-03 | R1 · QR-02 | 1 | OPEN limit і стан OPEN | Functional | System | P1 | LIMIT_OPEN → стан OPEN, relay OFF; C з OPEN запускає CLOSING (R6, R15) | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| TM-04 | R1 · QR-02 | 1 | Обидва limit switch активні; RESET у ERROR і поза ним | Functional, recovery | System | P1 | ERROR один раз, relay OFF, без циклу повідомлень; RESET у ERROR → CLOSED; RESET поза ERROR нічого не змінює (R10–R12) | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| TM-05 | R1 · QR-02 | 1 | LED після STOP, diagnostic для некоректних команд, одна команда на натискання | Functional, reliability | Component | P2 | OPEN LED OFF у STOPPED; diagnostic друкується; одне натискання — один COMMAND (R13, R14, R16) | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| TM-06 | R3 · QR-03 | 3 | Межі довжини рядка: 40, 41, 200, 1000 символів | Boundary / negative | Interface / protocol | P1 | 40 — команда; 41+ → «ERROR: command too long»; без SYSTEM FAULT і reboot (REQ-11, 12, 14, 16) | [TC-27.log](../../logs/task3_uart_cli/TC-27.log) |
| TM-07 | R1 · QR-03 | 3 | Валідація значень і синтаксису CLI: speed 256 / −1 / 999, timeout 0 / 61 / −5, HELP vs Status, спецсимволи | Boundary / negative | Component | P2 | Невалідний ввід → «ERROR», значення збережене; регістр команд за правилом (REQ-03, 05, 06, 08) | [TC-10](../../logs/task3_uart_cli/TC-10.log), [TC-17](../../logs/task3_uart_cli/TC-17.log), [TC-21](../../logs/task3_uart_cli/TC-21.log), [TC-24](../../logs/task3_uart_cli/TC-24.log) |
| TM-08 | R4 · QR-04 | 5 | Persistent counter після powerloss під час save | Persistence, recovery | Recovery / fault injection | P1 | Старе значення або old+1; пошкодження залоговано; 5 з 5 запусків (R6) | [serial log Task 5](../../logs/task5_recovery/serial_20261014_152215.log) |
| TM-09 | R5 · QR-05 | 7 | Overflow offline buffer: NET DOWN, SEND ×8, ×9, ×12, STRESS 100 | Network stress, boundary | Network | P1 | buffer ≤ 8; для 12 повідомлень buffer=8, dropped=4; DROP_OLDEST залоговано й застосовано (R4) | [device-monitor log](../../logs/task7_network_memory/device-monitor-261024-174403.log) |
| TM-10 | R5 · QR-05 | 7 | Flush після NET UP зі слідкуванням за message ID | Functional, network stress | Network | P1 | Кожен ID один раз, від найстарішого; duplicates=0; втрачені лише ID з лічильника dropped (R5, R6, R8) | [device-monitor log](../../logs/task7_network_memory/device-monitor-261024-174403.log) |
| TM-11 | R6 · QR-06 | 7 | Memory stability: RESET STATS, STRESS 100 ×10, 20 циклів reconnect | Memory stability | System | P1 | Втрата heap менша за 5%; без стабільної втрати на повідомлення чи reconnect (R7) | [heap trend](../../screenshots/task7_heap_trend.png), [network_stress.csv](../../logs/network_stress.csv) |
| TM-12 | R1 · QR-07 | 2 | Sweep імпульсу NOISE: 0.5, 1, 2, 10, 20, 29, 30 мс | Boundary, automation | Component | P2 | Нижче порогу → 0 events, 0 actions; реальне натискання → 1 event і 1 action (AC4, AC5) | [bt01](../../logs/task2_debounce/bt01_pulse_1ms_run1.log), [bt03](../../logs/task2_debounce/bt03_pulse_10ms_run1.log) |
| TM-13 | R1 · QR-07 | 2 | Шум під час critical action; пауза 15 мс між натисканнями | Reliability, automation | Component | P2 | Шум не додає event; Actions = кількість реальних натискань | [tc06](../../logs/task2_debounce/tc06_noise_in_critical_run1.log), [tc14](../../logs/task2_debounce/tc14_gap_15ms_run1.log), [tc23](../../logs/task2_debounce/tc23_noise_during_action_run1.log) |
| TM-14 | R2 · QR-08 | 4 | I2C після NACK: FAULT on → off у відомий момент, capture ≥ 30 с | Protocol, recovery | Interface / protocol | P2 | Retry або повідомлення про втрату; опитування 0x68 відновлюється; без тиші 33 с | [i2c_failure.sr](../../test-results/i2c_failure.sr) |
| TM-15 | R1 · QR-09 | 6 | JSON-протокол: валідність, SET PWM 0 / 1 / 99 / 100 / 101, RESET після SET LED ON і SET PWM 50 | Protocol, boundary | Interface / protocol | P2 | json.loads для кожної відповіді; PWM 0–100 → OK, 101 → INVALID_VALUE; RESET → led=false, pwm=0 | [pytest_output.txt](../../test-results/task6_protocol/pytest_output.txt), [manual_check_1.log](../../logs/task6_protocol/manual_check_1.log) |
| TM-16 | R1 · QR-09 | 6 | Час відповіді PING і STATUS | Protocol, reliability | Interface / protocol | P3 | Порівнянний час; STATUS після PING не затримується (ліміт погодити з власником вимог) | [test_ping_is_not_an_outlier_vs_status.log](../../logs/task6_protocol/pytest_cases/tests_test_candidates_bugs.py_test_ping_is_not_an_outlier_vs_status.log) |
| TM-17 | R3 · QR-10 | 5 | sleep N = 3, 5, 10, 20, 60 с за часом firmware | Recovery | Recovery / fault injection | P2 | Wake-up у межах N ±15% за таймером; 60 с не завершується INT_WDT | [serial log Task 5](../../logs/task5_recovery/serial_20261014_152215.log), [pytest_log_task5.pdf](../../test-results/task5_recovery/pytest_log_task5.pdf) |
| TM-18 | R3 · QR-10 | 5 | Watchdog: hang, вимірювання часу до reset | Recovery | Recovery / fault injection | P2 | Reset за 5 с ±15% (firmware: 4000 мс), reset reason INT_WDT, нормальний старт | [serial log Task 5](../../logs/task5_recovery/serial_20261014_152215.log), [pytest_log_task5.pdf](../../test-results/task5_recovery/pytest_log_task5.pdf) |
| TM-19 | R3 · QR-10 | 5 | Некоректні аргументи sleep: порожній, 0, abc, 3.5.1, −5, 99999999999 | Boundary / negative | Component | P3 | Повідомлення про помилку, значення не збережене, sleep не запускається | [pytest_log_task5.pdf](../../test-results/task5_recovery/pytest_log_task5.pdf) |
| TM-20 | R5 · QR-11 | 7 | Backoff під час 20-секундного outage | Network stress | Network | P3 | Не більше 12 retry за 20 с із зростаючим backoff; reconnect за кілька секунд після NET UP (R2) | [device-monitor-261025-000245.log](../../logs/task7_network_memory/device-monitor-261025-000245.log) (рядки 2739–2744) |
| TM-21 | R5 · QR-05, QR-11 | 7 | Некоректні аргументи STRESS, повторні fault-команди | Boundary / negative | Component | P3 | «[CLI] ERROR»; повторний NET DOWN або NET UP у тому ж стані нічого не змінює (R1, R2, R8) | [device-monitor-261025-000245.log](../../logs/task7_network_memory/device-monitor-261025-000245.log) |
| TM-22 | R1–R6 · QR-12 | 1–7 | Закрити open requirement questions і повторити TM-01, 08, 14 на real hardware | Functional, protocol, recovery | System (real hardware) | P3 | Кожне open question має рішення; три ключові тести проходять на стенді з виміряним, а не симульованим часом | — |

Покриття: **22 тести (9 × P1, 8 × P2, 5 × P3)**.

## 4. Фактичні результати та трасування до defects

| Test ID | Результат | Фактичний результат (Actual) | Defects |
|---|---|---|---|
| TM-01 | FAIL | CLOSING → OPENING напряму; relay перекриваються в 4 із 5 запусків | T1-06, T1-09 |
| TM-02 | FAIL | Timeout у CLOSING працює, в OPENING стан не переходить у ERROR | T1-01 |
| TM-03 | FAIL | OPEN недосяжний; «OPEN LIMIT DETECTED» 155 разів, relay лишається ON | T1-02, T1-03 |
| TM-04 | FAIL | Warning loop замість ERROR; RESET не очищає; RESET поза ERROR змінює стан на CLOSED | T1-07, T1-10, T1-11 |
| TM-05 | FAIL | OPEN LED лишається ON після STOP; некоректна команда без diagnostic; 3–6 команд на натискання | T1-04, T1-05, T1-08, T1-12 |
| TM-06 | FAIL | 40 символів — норма; 41+ → SYSTEM FAULT і reboot, 26 з 26 | T3-05 |
| TM-07 | FAIL | speed 256 → 255; timeout 0 прийнято; `Status` виконується; спецсимволи → OK (значення −1, 999, 100000, 61, −5 відхилено правильно) | T3-01…T3-04 |
| TM-08 | FAIL | Counter 8 → 108; серія 730 → 831 … 1134 → 1234, без повідомлення про пошкодження | T5-01 |
| TM-09 | FAIL | buffer=12, dropped=0 (рівно 8 — коректно) | T7-03 |
| TM-10 | FAIL | 24 publish для 12 повідомлень, ID 11–14 не опубліковано; лічильник duplicates розходиться з логом | T7-02, T7-05 |
| TM-11 | FAIL | Heap 344 924 → 264 920 B (−80 004 B, −23.2%) | T7-04 |
| TM-12 | FAIL | 0.5 і 1 мс ігноруються; від 2 мс приймаються як натискання (5 з 5) | T2-01 |
| TM-13 | FAIL | Шум під час action додає зайву logical event (RAW 139–162, events 2, actions 2); пауза 15 мс дає 2 events | T2-01 |
| TM-14 | FAIL | NACK на 0x69 у 609.122546 с, потім 33.09 с без активності на шині | T4-01, T4-02 |
| TM-15 | FAIL | RESET → OK, але led=true, pwm=127; GET TEMP без `}`; PWM 100 → INVALID_VALUE (0–99 і 101 — коректно) | T6-01, T6-02, T6-03 |
| TM-16 | FAIL | PING 1.31–1.40 с, медіана у 5.7 раза більша за STATUS; control-тест проходить | T6-04 |
| TM-17 | FAIL | Wake-up 0.41 / 0.59 / 0.70 / 0.71 с незалежно від N; sleep 60 с → INT_WDT | T5-02, T5-05 |
| TM-18 | FAIL | Watchdog reset через 14.59 с замість 5 с | T5-03 |
| TM-19 | FAIL | 18 з 18 випадків без помилки; значення мовчки підміняються | T5-04 |
| TM-20 | FAIL | 391 retry за 20 с, backoff 500 мс один раз, далі 50 мс | T7-01 |
| TM-21 | FAIL | STRESS −5 / 1.5 / abc виконуються як count=1; повторний NET DOWN входить у DISCONNECTED знову | T7-06, T7-07 |
| TM-22 | NOT EXECUTED | Потрібен real hardware | — |

Підсумок: **21 тест FAIL, 1 не виконано**; кожен із 36 defects має щонайменше один рядок матриці.

## 5. Покриття за ризиками та проєктами

| Quality Risk | R | Тести | Tasks | Priority |
|---|---|---|---|---|
| QR-01 | R1 | TM-01 | 1 | P1 |
| QR-02 | R1 | TM-02, 03, 04, 05 | 1 | P1 |
| QR-03 | R1, R3 | TM-06, 07 | 3 | P1 |
| QR-04 | R4 | TM-08 | 5 | P1 |
| QR-05 | R5 | TM-09, 10, 21 | 7 | P1 |
| QR-06 | R6 | TM-11 | 7 | P1 |
| QR-07 | R1 | TM-12, 13 | 2 | P2 |
| QR-08 | R2 | TM-14 | 4 | P2 |
| QR-09 | R1 | TM-15, 16 | 6 | P2 / P3 |
| QR-10 | R3 | TM-17, 18, 19 | 5 | P2 / P3 |
| QR-11 | R5 | TM-20, 21 | 7 | P3 |
| QR-12 | R1–R6 | TM-22 | 1–7 | P3 |

| Task | Проєкт | Тести | Defects |
|---|---|---|---|
| 1 | Smart Gate Controller | TM-01…05 | 12 |
| 2 | Button Debounce | TM-12, 13 | 1 |
| 3 | UART CLI | TM-06, 07 | 5 |
| 4 | I2C sensor polling | TM-14 | 2 |
| 5 | Recovery / Fault Injection | TM-08, 17, 18, 19 | 5 |
| 6 | JSON serial protocol | TM-15, 16 | 4 |
| 7 | IoT network / memory | TM-09, 10, 11, 20, 21 | 7 |

## 6. Обмеження матриці

- Матриця виконана в симуляторах; TM-22 (real hardware) ще не виконано.
- Пороги в Expected Result (debounce ≈ 30 мс, 12 retry за 20 с, 5% heap, ±15% часу) — припущення тестувальника, а не вимоги; для I2C recovery і latency PING вимог немає.
- Рівня Integration testing із вебінару в матриці немає: збірки тестувалися окремо.
- Для R2 збій DHT22 не тестувався, для R4 стан після crash у Task 3 не перевірявся.
