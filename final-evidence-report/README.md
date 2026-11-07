# Embedded QA Final Report — Smart IoT Safety Controller (Tasks 1–7)

Фінальний evidence package з портфоліо Embedded QA: Master Test Plan, результати тестів, логи, автотести та скріншоти для семи embedded / IoT збірок. Автор: Serhii, QA Embedded Engineer · 2026-11-01.

**Результат:** 36 defects, release recommendation — **NO-GO** (9 Blocker / Critical defects).

## Як користуватись

1. Почніть із [master-test-plan.md](./master-test-plan.md): scope, ризики R1–R6, Test Matrix, Entry / Exit Criteria, регресія, рішення.
2. Для кожного висновку перевірте evidence за [test-results/reports/EVIDENCE_INDEX_UA.md](./test-results/reports/EVIDENCE_INDEX_UA.md): там є conclusion і команда перевірки.
3. Історія «від проблеми до результату» — у [test-results/reports/case_study_UA.md](./test-results/reports/case_study_UA.md), оцінка ризиків — у [Risk_Matrix_UA.md](./test-results/reports/Risk_Matrix_UA.md), статистика тестів — у [test_summary.md](./test-results/reports/test_summary.md), Test Matrix (Крок 2) — у [Test_Matrix_UA.md](./test-results/reports/Test_Matrix_UA.md), рішення про release — у [Release_Decision_UA.md](./test-results/reports/Release_Decision_UA.md), висновок QA — у [QA_Conclusion_UA.md](./test-results/reports/QA_Conclusion_UA.md).

## Структура пакета

```
final-report/
├── README.md                    опис звіту, зміст, як користуватись
├── master-test-plan.md          план тестування та критерії
├── test-results/                результати тестів (логи, тести, артефакти)
│   ├── i2c_failure.sr           трасування I2C збоїв (Task 4, відкривається в PulseView)
│   ├── task1_gate/ … task7_network_memory/   звіти й test sheets по Tasks
│   └── reports/                 Risk Matrix, Case Study, Evidence Index, Test Summary
├── logs/                        логи тестів та системи
│   ├── network_stress.csv       дані стрес-тестів мережі (166 рядків зі STATUS-логів Task 7)
│   └── task2_debounce/ … task7_network_memory/   сирі логи
├── tests/                       скрипти та тести
│   ├── pytest/                  Python-тести й helpers (Task 6, Task 7)
│   └── wokwi_scenarios/         YAML-сценарії Wokwi CLI (Task 3)
└── screenshots/                 скріншоти графіків і виводу (див. примітку)
```

Примітка про `screenshots/`: це PNG-рендери PDF-експортів terminal (Tasks 4–7) і графік heap, побудований із логів Task 7 (`task7_heap_trend.png`). Скріншотів самого вікна Wokwi в архіві немає.

## Project goal

Підтримати рішення про release: чи безпечні, відновлювані й стабільні сім firmware-збірок (ворота, debounce, UART CLI, I2C, recovery, JSON-протокол, IoT network / memory). Тестування — risk-based: від ризику до доказу.

## System under test

| Task | Збірка | Платформа |
|---|---|---|
| 1 | Smart Gate Controller | Arduino Uno, 2 relay, limit switches |
| 2 | Button Debounce | ESP32, BUTTON, NOISE |
| 3 | UART CLI Homework Device v2.0 | ESP32 |
| 4 | I2C sensor polling | ESP32 + MPU-6050 |
| 5 | Recovery / Fault Injection | ESP32 DevKit V1, relay, DHT22 |
| 6 | JSON serial protocol (BUGGY) | ESP32, LED, PWM |
| 7 | IoT network / memory stability | ESP32 + DHT22, MQTT broker (симуляція) |

Версії FW / HW: назви збірок і banner (v2.0, homework_buggy, BUGGY); ELF SHA256 `1e9f6d28d20fb872` — лише для Task 5.

## Test strategy

Критичні ризики R1–R6: неправильна команда керування, датчик недоступний, зависання прошивки, втрата живлення під час збереження, мережа недоступна, деградація пам'яті. Для них побудовано Test Matrix із 22 тестів (9 × P1, 8 × P2, 5 × P3), рівні: component / interface, system black-box, fault injection, non-functional / reliability, automation / regression. Критерії успіху — Exit Criteria в `master-test-plan.md` (розділ 12).

## Environment & tools

Wokwi 3.7.0, Wokwi CLI v0.27.1, PlatformIO IDE 3.3.2, logic analyzer (sigrok / PulseView), Python 3.9.12, pytest 8.4.2, pyserial (RFC2217), симульований MQTT broker. Хост: macOS 12, MacBook Pro mid-2015.

## Key scenarios

1. Реверс воріт без safe stop → обидва relay HIGH (Task 1).
2. Sweep імпульсу NOISE 0.5–30 мс → поріг debounce 1–2 мс замість ≈30 мс (Task 2).
3. UART-рядок із 41 символу → SYSTEM FAULT і reboot (Task 3).
4. I2C NACK → 33.09 с тиші на шині (Task 4).
5. Powerloss під час save → counter 8 → 108 (Task 5).
6. Offline buffer: SEND ×12 → 24 publish, втрачені ID, heap −23.2% (Task 7).

## Bugs / findings

| Task | Defects | Severity як зафіксовано |
|---|---|---|
| 1 | 12 | 5 Blocker, 3 Major, 3 Minor, 1 «Intermittent» |
| 2 | 1 | 1 Major |
| 3 | 5 | 1 Critical, 4 Major |
| 4 | 2 | 2 High |
| 5 | 5 | 3 Major (High), 2 Medium |
| 6 | 4 | 2 High, 1 Medium, 1 Low / Medium |
| 7 | 7 | 3 Critical, 2 Major, 1 Minor, 1 Trivial |

Повний реєстр — Appendix A у `master-test-plan.md`. Найважливіше: перекриття relay (T1-06, T1-09), crash від довгого рядка (T3-05), counter +100 після powerloss (T5-01), overflow, дублікати й витік heap (T7-03…05).

## Evidence

Логи (`logs/`), trace I2C (`test-results/i2c_failure.sr`), pytest-звіти (`test-results/task6_protocol/pytest_output.txt`, PDF для Tasks 5 і 7), метрики heap та мережі (`logs/network_stress.csv`, `screenshots/task7_heap_trend.png`), bug reports (xlsx / HTML у `test-results/`), test summary. Прогалини: Wokwi-скріншоти й відео, файли проєкту Wokwi (diagram.json), SPI-тести.

## What I learned / decisions made

- Ризик визначає глибину тестів: шість ризиків зі score 9 тестувалися першими й із повторами від 4/5 до 26/26.
- Severity і reproducibility — різні поля (урок із T1-07, де «Intermittent» записано як severity).
- Пороги без вимог (debounce, latency PING, I2C recovery) я позначив як припущення й виніс в open questions, а не видав за requirements.
- Failed pytest ≠ firmware bug: частина результатів — ERROR (Tasks 5 і 6; це проблема виконання тесту, а не доведений firmware bug) або тести, написані для виявлення підозрілого bug; причину доводив ланцюжком test logic → environment → communication → requirement → firmware.
- Наступні кроки: Wokwi-скріншоти, повторний Task 4 із FAULT off, перевірка Task 5 за часом firmware, прогін на real hardware.

## Як відповідати на співбесіді (за матеріалами проєкту)

| Питання | Відповідь на основі проєкту |
|---|---|
| Пристрій працює у Wokwi. Навіщо real hardware? | Симуляція підтвердила логіку (наприклад, T1-09, T5-01), але не показує timing, noise, power behavior і реальні умови інтерфейсів: simulator clock у Task 5, contact bounce як атрибут симуляції, powerloss як команда, а не brown-out. |
| Автотест FAILED. Це firmware bug? | Не одразу: test logic → environment → communication → requirement → firmware. У проєкті TC-15 (Task 7) — помилка тесту, pytest ERROR у Tasks 5 і 6 — не assertion firmware, а T6-03 підтверджено ще й вручну (`logs/task6_protocol/manual_check_1.log`). |
| Як протестувати без повної документації? | Виділити observable inputs / outputs, зібрати known constraints, зафіксувати assumptions (debounce ≈ 30 мс, 12 retry за 20 с), будувати risk-based exploratory сценарії й не видавати припущення за requirements (Task 4 без вимог). |
