# Task 5 — Recovery / Fault Injection (pytest)

## Project goal

Перевірити відновлення пристрою після збоїв: powerloss під час збереження, зависання (watchdog), deep sleep, некоректні аргументи.

## System under test

ESP32 DevKit V1, relay, DHT22; збірка «homework_buggy» (ELF SHA256 1e9f6d28d20fb872). Команди sleep, hang, powerloss, status; task watchdog 4000 мс; persistent counter.

## Test strategy

Risk-based: QR-04 (score 9, P1) і QR-10 (score 6, P2). Fault injection (`powerloss`, `hang`), перевірка counter до / після, час wake-up і watchdog, некоректні аргументи sleep. Тести: TM-08, TM-17, TM-18, TM-19.

## Environment & tools

Python 3.9.12, pytest 8.4.2 (pytest-html 4.2.0), pyserial через RFC2217, Wokwi CLI v0.27.1; macOS 12.

## Key scenarios

1. `powerloss` під час save: counter 8 → 108 (5 з 5; серія 730 → 831 … 1134 → 1234), повідомлення про пошкодження немає.
2. `sleep N` для N = 3, 5, 10, 20: wake-up 0.41–0.71 с замість N ±15%.
3. `hang`: watchdog reset через 14.59 с замість 5 с, reset reason INT_WDT.
4. `sleep` з некоректними аргументами (порожній, 0, abc, 3.5.1, −5, 99999999999): підміна значень без помилки.

## Bugs / findings

Severity як зафіксовано в Task: 3 Major (High), 2 Medium. Усього defects: 5.

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T5-01 | Перерване збереження лишає counter = old+100, не виявлено | Major (High) | 5/5 | Старе значення або old+1, пошкодження залоговано (R6) | Counter +100 (8 → 108; 730 → 831 …), повідомлення немає |
| T5-02 | Час wake-up ігнорує задану тривалість sleep | Major (High) | 5/5 | Wake-up за N ±15% (R4) | 0.41 / 0.59 / 0.70 / 0.71 с для N = 3 / 5 / 10 / 20 |
| T5-03 | Watchdog reset через ≈14.6 с замість 5 с | Major (High) | 1 вимірювання | Reset за ≈5 с (R5) | 14.59 с, reset reason INT_WDT, firmware повідомляє 4000 мс |
| T5-04 | sleep приймає некоректні аргументи й мовчки підміняє значення | Medium | 18/18 | Повідомлення про помилку, без збереження стану | Підміна на 1, 3, 5 або 60 с; [STORE] saved друкується |
| T5-05 | 60-секундний sleep завершується watchdog reset | Medium | 6/6 | Wake-up за таймером | TG1WDT_SYS_RESET, reset_reason INT_WDT |

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [pytest_log_task5.pdf](pytest_log_task5.pdf) — 49 тестів: 26 failed, 18 passed, 4 skipped, 1 error (467.53 с)
- [logs/serial_20261014_152215.log](logs/serial_20261014_152215.log) — serial log (counter: рядки 173–187; watchdog: рядки 138–157)
- [Recovery_Fault_Injection_Test_Sheet_Webinar_5_UA.pdf](Recovery_Fault_Injection_Test_Sheet_Webinar_5_UA.pdf), [test_cases_by_group.md](test_cases_by_group.md), [report.html](report.html)
- [serial_monitor_task5.pdf](serial_monitor_task5.pdf), скріншоти: [pytest log](screenshots/task5_pytest_log.png), [serial monitor](screenshots/task5_serial_monitor.png)

Прогалини: файли test_*.py для Task 5 відсутні в архіві; стан relay після watchdog reset не перевірений (`test_actuator_off_after_wdt` завершився ERROR).

## What I learned / decisions made

- Failed pytest ≠ firmware bug: ERROR треба розслідувати за ланцюжком test logic → environment → communication → requirement → firmware.
- Час у Task 5 виміряно за simulator clock і потребує підтвердження за часом firmware.
- `powerloss` — це fault injection, а не справжній brown-out; висновки про електрику потребують real hardware.
