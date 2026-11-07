# Bug Register — Embedded QA (Tasks 1–7)

Звіти про знайдені дефекти та відтворення: реєстр усіх 36 defects із expected / actual. Підготував Serhii, QA Embedded Engineer, 2026-11-01. Кожен defect має steps, evidence і логи у вихідних звітах свого Task (таблиця нижче) та в [Consolidated Bug Report — Embedded QA (Tasks 1–7)](../Consolidated%20Bug%20Report%20%E2%80%94%20Embedded%20QA%20(Tasks%201%E2%80%937).md).

Severity збережено як у кожному Task (шкали різні). Reproducibility — окреме поле, не severity.

## Джерела за проєктами

| Task | Проєкт | Defects | Severity як зафіксовано | Вихідні звіти та evidence |
|---|---|---|---|---|
| 1 | Smart Gate Controller | 12 | 5 Blocker, 3 Major, 3 Minor, 1 «Intermittent» | [Bug_Report xlsx](task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx), [PDF](task1_gate/Serhii%20Shtelmakh%20Task%201.pdf) |
| 2 | Button Debounce | 1 | 1 Major | [verdicts.md](../wokwi/task2_debounce/verdicts.md), [test_cases](../wokwi/task2_debounce/test_cases_Serhii_Shtelmakh.md), [логи](../wokwi/task2_debounce/logs/) |
| 3 | UART CLI | 5 | 1 Critical, 4 Major | [HTML-звіт](../wokwi/task3_uart_cli/Task3_test_and_bug_report.html), [логи TC-01…36](../wokwi/task3_uart_cli/logs/) |
| 4 | I2C sensor polling | 2 | 2 High | [QA Conclusion PDF](../pulseview/task4_i2c/QA_Conclusion_I2C_trace_ESP32_MPU6050.pdf), [i2c_failure.sr](../pulseview/task4_i2c/i2c_failure.sr) |
| 5 | Recovery / Fault Injection | 5 | 3 Major (High), 2 Medium | [Test Sheet PDF](../pytest/task5_recovery/Recovery_Fault_Injection_Test_Sheet_Webinar_5_UA.pdf), [serial log](../pytest/task5_recovery/logs/serial_20261014_152215.log) |
| 6 | JSON serial protocol | 4 | 2 High, 1 Medium, 1 Low / Medium | [Test Sheet docx](../pytest/task6_protocol/Python_Pytest_Test_Sheet_Webinar_6_filled.docx), [pytest_output.txt](../pytest/task6_protocol/pytest_output.txt), [manual log](../pytest/task6_protocol/logs/manual_check_1.log) |
| 7 | IoT network / memory | 7 | 3 Critical, 2 Major, 1 Minor, 1 Trivial | [Test Sheet PDF](../network-stress/task7_network_memory/IoT_Network_Memory_Test_Sheet_Webinar_7_UA.pdf), [логи](../network-stress/task7_network_memory/logs/), [network_stress.csv](../network-stress/network_stress.csv) |

## Реєстр defects

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T1-01 | Movement timeout не переводить OPENING → ERROR | Major | 5/5 | OPENING без limit понад 10 с → ERROR (timeout) | Лишається OPENING (у CLOSING timeout працює) |
| T1-02 | OPEN limit не переводить ворота в OPEN | Blocker | 5/5 | LIMIT_OPEN → стан OPEN, relay OFF | «OPEN LIMIT DETECTED» 155 разів, relay лишається ON, стан не змінюється |
| T1-03 | Стан OPEN недосяжний, R15 неможливо перевірити | Blocker | 5/5 | У стані OPEN обидва relay OFF (R15) | OPEN ніколи не досягається, перевірка неможлива |
| T1-04 | OPEN LED лишається ON після STOP з OPENING | Minor | 5/5 | OPEN LED OFF у STOPPED (R14) | LED лишається ON |
| T1-05 | OPEN LED лишається ON після STOP з CLOSING | Minor | 5/5 | OPEN LED OFF у STOPPED (R14) | LED лишається ON |
| T1-06 | Протилежна команда реверсує напрямок без safe stop | Blocker | 5/5 | CLOSING → STOPPED → OPENING (R4) | CLOSING → OPENING напряму (і навпаки) |
| T1-07 | Обидва limit switch активні: warning loop замість ERROR | «Intermittent» (потрібна переоцінка) | 5/5 | Обидва limit активні → ERROR (R10) | «WARNING: both limit switches active» і нескінченний цикл «OPEN LIMIT DETECTED» |
| T1-08 | Некоректна команда в CLOSED мовчки ігнорується | Minor | 5/5 | Diagnostic-повідомлення для некоректної команди (R13) | Жодного повідомлення |
| T1-09 | Обидва relay короткочасно активні під час реверсу | Blocker | 4/5 | Relay ніколи не HIGH одночасно (R8) | relayOpen (pin 8) HIGH на один цикл раніше, ніж relayClose (pin 9) стає LOW |
| T1-10 | RESET поза ERROR змінює стан | Major | 5/5 | RESET поза ERROR нічого не змінює (R12) | Стан завжди стає CLOSED |
| T1-11 | RESET не очищає цикл limit switch | Blocker | 5/5 | RESET виводить з помилки (R10, R11) | Цикл повідомлень триває, OPEN relay ON; допомагає лише перезапуск симуляції |
| T1-12 | Нульовий debounce: одне натискання — кілька команд | Major | 5/5 | Одне натискання — одна команда (R16) | 3–6 рядків COMMAND (bounce = 0 у diagram.json) |
| T2-01 | NOISE-імпульси від 2 мс приймаються як натискання | Major / High | 5/5 | Імпульси нижче порогу (≈30 мс) → 0 events, 0 actions (AC4, AC5) | З 2 мс: Logical events 1, Actions 1; ефективний поріг 1–2 мс |
| T3-01 | set speed 256 прийнято й встановлено в 255 | Major / Medium | 5/5 | ERROR, speed лишається 77 (REQ-03) | «OK: speed=255» |
| T3-02 | set timeout 0 прийнято | Major / Medium | 5/5 | ERROR, timeout лишається 33 (REQ-05) | «OK: timeout=0» |
| T3-03 | status не case-insensitive | Major / Medium | 5/5 | Регістр команд за правилом: HELP і Status → ERROR (REQ-06) | HELP → ERROR, але Status виконується |
| T3-04 | Рядок лише зі спецсимволів прийнято як валідну команду | Major / Medium | 5/5 | «ERROR: unknown command» (REQ-08) | «OK» |
| T3-05 | Ввід довший за 40 символів валить і перезавантажує пристрій | Critical / High | 5/5 (26/26) | «ERROR: command too long», пристрій працює (REQ-11, 12, 14, 16) | «*** SYSTEM FAULT ***», SW_CPU_RESET, reboot |
| T4-01 | Після першого NACK пристрій припиняє всю I2C-активність | High | 1/1 capture | Продовження опитування або повідомлення про помилку | NACK на 0x69 у 609.122546 с, далі 33.09 с без активності |
| T4-02 | Після NACK не видно recovery чи reboot | High (proposed) | 1/1 capture | Видимий recovery (retry, re-init 0x6B, reboot) | Жодного обміну з 0x68, жодного запису в 0x6B |
| T5-01 | Перерване збереження лишає counter = old+100, не виявлено | Major (High) | 5/5 | Старе значення або old+1, пошкодження залоговано (R6) | Counter +100 (8 → 108; 730 → 831 …), повідомлення немає |
| T5-02 | Час wake-up ігнорує задану тривалість sleep | Major (High) | 5/5 | Wake-up за N ±15% (R4) | 0.41 / 0.59 / 0.70 / 0.71 с для N = 3 / 5 / 10 / 20 |
| T5-03 | Watchdog reset через ≈14.6 с замість 5 с | Major (High) | 1 вимірювання | Reset за ≈5 с (R5) | 14.59 с, reset reason INT_WDT, firmware повідомляє 4000 мс |
| T5-04 | sleep приймає некоректні аргументи й мовчки підміняє значення | Medium | 18/18 | Повідомлення про помилку, без збереження стану | Підміна на 1, 3, 5 або 60 с; [STORE] saved друкується |
| T5-05 | 60-секундний sleep завершується watchdog reset | Medium | 6/6 | Wake-up за таймером | TG1WDT_SYS_RESET, reset_reason INT_WDT |
| T6-01 | SET PWM 100 повертає INVALID_VALUE | Medium | 5/5 | {"status":"OK","pwm":100} (Req. 5) | {"status":"ERROR","code":"INVALID_VALUE"} |
| T6-02 | RESET відповідає OK, але не скидає LED і PWM | High | 5/5 | led=false, pwm=0 (Req. 7) | led=true, pwm=127 (або 255) |
| T6-03 | GET TEMP повертає invalid JSON | High | 100% | Валідний JSON (Req. 3) | {"status":"OK","temperature":24.5 без закривної дужки |
| T6-04 | PING блокує обробку команд приблизно 1.3 с | Low / Medium | 100% | PING відповідає швидко, як STATUS | 1.31–1.40 с; медіана у 5.7 раза більша за STATUS |
| T7-01 | Reconnect storm, приблизно 19 retry на секунду | Major / Medium | 5/5 | Не більше 12 retry за 20 с, зростаючий backoff (R2) | 391 retry за 20 с, backoff 500 мс один раз, далі 50 мс |
| T7-02 | Кожне буферизоване повідомлення публікується двічі після NET UP | Major / Medium | 6/6 | Кожен ID один раз, duplicates=0 (R6) | Кожен ID двічі (12 повідомлень → 24 publish) |
| T7-03 | Buffer росте понад capacity 8, нічого не відкидається | Critical / High | 4/4 | buffer=8, dropped=4 для 12 повідомлень (R4) | buffer=12, dropped=0 |
| T7-04 | Витік heap, 80 B на повідомлення | Critical / High | 5/5 | Втрата heap менша за 5% (R7) | −80 004 B (−23.2%) за 10 × STRESS 100 |
| T7-05 | Flush після overflow губить найстаріші повідомлення й повторює інші | Critical / High | 4/4 | 8 найновіших ID по одному разу, від найстарішого | 24 publish; ID 19–22 чотири рази, 15–18 двічі, ID 11–14 не опубліковано |
| T7-06 | Некоректні аргументи STRESS мовчки виконуються як count=1 | Minor / Low | 2 запуски | «[CLI] ERROR» (R2, R8) | Виконується з count=1 без помилки |
| T7-07 | Fault-команди не є idempotent | Trivial / Low | 2 запуски | Повторна команда у тому ж стані нічого не змінює (R1, R8) | Повторний NET DOWN знову входить у DISCONNECTED, retry зростає |

Підсумок: 36 defects, з них 9 Blocker / Critical (T1-02, 03, 06, 09, 11; T3-05; T7-03, 04, 05). Рекомендація: **NO-GO** ([Release_Decision_UA.md](../Release_Decision_UA.md)).
