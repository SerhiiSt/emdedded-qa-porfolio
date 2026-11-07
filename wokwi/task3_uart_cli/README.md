# Task 3 — UART CLI Homework Device v2.0 (Wokwi CLI)

## Project goal

Перевірити UART-інтерфейс командного рядка: граматику команд, валідацію значень, обробку надто довгого вводу й конфігурацію (REQ-01…REQ-16).

## System under test

ESP32, UART console, команди help, status, set speed, set timeout, led; стан CONFIG SAVED / DIRTY; ліміт рядка 40 символів. Firmware v2.0 (banner «UART CLI HOMEWORK DEVICE v2.0»).

## Test strategy

Risk-based: QR-03 (score 9, P1). Boundary і negative тести: значення поза діапазоном, регістр команд, спецсимволи, довжина рядка 40 / 41 / 200 / 1000. Тести: TM-06, TM-07; 36 сценаріїв TC-01…TC-36.

## Environment & tools

Wokwi CLI v0.27.1, scenario YAML з очікуваним виводом; логи кожного сценарію.

## Key scenarios

1. 41 символ: `*** SYSTEM FAULT ***`, SW_CPU_RESET, reboot (26 з 26 спроб; 40 символів — норма).
2. `set speed 256` → `OK: speed=255` замість ERROR.
3. `set timeout 0` → `OK: timeout=0` замість ERROR.
4. `HELP` → ERROR, але `Status` виконується.
5. Рядок лише зі спецсимволів → `OK` замість `ERROR: unknown command`.

## Bugs / findings

Severity як зафіксовано в Task: 1 Critical, 4 Major. Усього defects: 5.

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T3-01 | set speed 256 прийнято й встановлено в 255 | Major / Medium | 5/5 | ERROR, speed лишається 77 (REQ-03) | «OK: speed=255» |
| T3-02 | set timeout 0 прийнято | Major / Medium | 5/5 | ERROR, timeout лишається 33 (REQ-05) | «OK: timeout=0» |
| T3-03 | status не case-insensitive | Major / Medium | 5/5 | Регістр команд за правилом: HELP і Status → ERROR (REQ-06) | HELP → ERROR, але Status виконується |
| T3-04 | Рядок лише зі спецсимволів прийнято як валідну команду | Major / Medium | 5/5 | «ERROR: unknown command» (REQ-08) | «OK» |
| T3-05 | Ввід довший за 40 символів валить і перезавантажує пристрій | Critical / High | 5/5 (26/26) | «ERROR: command too long», пристрій працює (REQ-11, 12, 14, 16) | «*** SYSTEM FAULT ***», SW_CPU_RESET, reboot |

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [Task3_test_and_bug_report.html](Task3_test_and_bug_report.html) — HTML-звіт про тести й bug reports
- [logs/](logs/) — 36 логів сценаріїв, ключовий [TC-27.log](logs/TC-27.log)
- [scenarios/](scenarios/) — 36 YAML-сценаріїв

Прогалини: підсумкові pass / fail по 36 сценаріях окремо не підраховані; втрату незбереженого стану після crash не перевірено.

## What I learned / decisions made

- Один defect може повторюватись у різних тестах: SYSTEM FAULT виникав у всіх сценаріях із довгим рядком (T3-05).
- Значення −1, 999, 100000, 61 і −5 відхиляються правильно — перевіряти межі з обох боків.
- Рішення: тримати окремий сценарій на кожну межу, щоб failure вказував на конкретну вимогу.
