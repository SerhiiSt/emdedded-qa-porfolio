# Task 2 — Button Debounce (Wokwi CLI)

## Project goal

Перевірити, що пристрій перетворює натискання кнопки на одну logical event і одну action та ігнорує шум (acceptance criteria AC1–AC5).

## System under test

ESP32, BUTTON, джерело NOISE, LED, watchdog. Serial Logger виводить RAW interrupts, Logical events і Actions.

## Test strategy

Risk-based: QR-07 (score 6, P2). Sweep ширини імпульсу NOISE 0.5, 1, 2, 10, 20, 29, 30 мс, шум під час critical action, пауза 15 мс між натисканнями, повтор 2 мс ×5 запусків. Тести: TM-12, TM-13.

## Environment & tools

Wokwi CLI v0.27.1, сценарії scenarios_v2 (*.test.yaml), verdict-скрипт. Хост: macOS 12.

## Key scenarios

1. Імпульс 1 мс: `RAW 2 · Logical events 0 · Actions 0` — ігнорується правильно.
2. Імпульс 10 мс: `Logical events 1 · Actions 1` — приймається як натискання.
3. Імпульс 2 мс, 5 запусків: 5 з 5 приймається.
4. Шум під час critical action та пауза 15 мс: `Logical events 2 · Actions 2` замість 1.

## Bugs / findings

Severity як зафіксовано в Task: 1 Major. Усього defects: 1.

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T2-01 | NOISE-імпульси від 2 мс приймаються як натискання | Major / High | 5/5 | Імпульси нижче порогу (≈30 мс) → 0 events, 0 actions (AC4, AC5) | З 2 мс: Logical events 1, Actions 1; ефективний поріг 1–2 мс |

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [verdicts.md](verdicts.md) — 38 verdict-рядків: 28 PASS, 7 FAIL, 2 REVIEW, 1 INVALID (TC-24 timed out)
- [summary.txt](summary.txt), [test_cases_Serhii_Shtelmakh.md](test_cases_Serhii_Shtelmakh.md)
- [logs/](logs/) — 43 логи запусків, наприклад [bt01](logs/bt01_pulse_1ms_run1.log), [bt03](logs/bt03_pulse_10ms_run1.log), [tc07 run 1](logs/tc07_repeat_noise_2ms_run1.log)

Прогалини: YAML-сценарії scenarios_v2 і VCD-сигнали не збережені; TC-25 (manual) не виконано.

## What I learned / decisions made

- Поріг debounce ≈ 30 мс — моє припущення; без вимоги це open question, а не доведений firmware bug.
- Повторні запуски (5/5) відділяють реальний defect від випадкового збою.
- Рішення: тестувати кожну ширину імпульсу окремо, а не один «шумовий» сценарій.
