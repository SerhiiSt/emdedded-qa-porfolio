# Task 1 — Smart Gate Controller (Wokwi)

## Project goal

Перевірити state machine воріт: керування двома relay, limit switches, movement timeout, RESET і кнопки. Рішення, яке підтримує тест: чи безпечні ворота й чи відновлюються вони після помилки (вимоги R1–R16).

## System under test

Arduino Uno, 2 relay (pin 8 — open, pin 9 — close), limit switches OPEN / CLOSE, 3 кнопки (open, close, stop), LED. Стани: CLOSED / OPENING / OPEN / CLOSING / STOPPED / ERROR. Команди по serial: O, C, S, RESET. Версія FW у архіві не зафіксована.

## Test strategy

Risk-based: ризики QR-01, QR-02 (score 9, P1). Методи: функціональні перевірки state machine, спостереження за pin-станом relay, послідовності limit switch і RESET, повтори 5 запусків для кожного сценарію. Тести: TM-01…TM-05 ([Test_Matrix_UA.md](../../Test_Matrix_UA.md)).

## Environment & tools

Wokwi 3.7.0 у VS Code з PlatformIO IDE 3.3.2; macOS 12, MacBook Pro mid-2015, Chrome 150, VS Code 1.136.

## Key scenarios

1. Реверс напрямку (O під час CLOSING): очікується CLOSING → STOPPED → OPENING, фактично CLOSING → OPENING; relay перекриваються в 4 з 5 запусків.
2. OPEN limit у OPENING: стан OPEN недосяжний.
3. Обидва limit switch активні: warning loop замість ERROR; RESET не виводить зі стану.
4. Movement timeout: працює в CLOSING, не працює в OPENING.
5. RESET поза ERROR і debounce кнопок (bounce = 0).

## Bugs / findings

Severity як зафіксовано в Task: 5 Blocker, 3 Major, 3 Minor, 1 «Intermittent». Усього defects: 12.

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

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [Bug_Report_Serhii_Shtelmakh.xlsx](../../bug-reports/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) — bug report зі steps, expected / actual
- [Smart_Gate_Serhii_Shtelmakh_Test_Design.xlsx](Smart_Gate_Serhii_Shtelmakh_Test_Design.xlsx) — test design
- [Serhii Shtelmakh Task 1.pdf](../../bug-reports/task1_gate/Serhii%20Shtelmakh%20Task%201.pdf) — підсумок на сторінці

Прогалини: немає raw serial log-файла (серійний вивід зафіксовано в xlsx) і файлів проєкту Wokwi (diagram.json).

## What I learned / decisions made

- Таймаут реалізовано асиметрично (CLOSING так, OPENING ні): перевіряти обидва напрямки.
- Один defect ховає інший: T1-03 (OPEN недосяжний) робить неможливою перевірку R15.
- «Intermittent» (T1-07) — це reproducibility, а не severity; ці поля треба вести окремо.
- Рішення: запустити сценарій реверсу 20 разів як regression gate для безпеки relay.
