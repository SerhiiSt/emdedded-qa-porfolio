# Embedded QA Portfolio — Smart IoT Safety Controller

GitHub-портфоліо з тестування Embedded / IoT: сім проєктів (Tasks 1–7), Master Test Plan, evidence, дефекти й рекомендація щодо release. Автор: Serhii, QA Embedded Engineer · 2026-11-01.

**Результат:** 36 defects, з них 9 Blocker / Critical, рекомендація — **NO-GO**. Артефакти показують логіку (ризик → тест → evidence → висновок), а не набір інструментів.

## Project goal

Підтримати рішення про release: чи безпечні, відновлювані й стабільні сім firmware-збірок (ворота, debounce, UART CLI, I2C, recovery, JSON-протокол, IoT network / memory). Тестування risk-based: від ризику до доказу. Метою було показати практичне тестування Embedded / IoT, аналіз ризиків, планування покриття, збір доказів і професійне оформлення QA-документації.

## System under test

Smart IoT Safety Controller — MCU-контролер (ESP32; у Task 1 — Arduino Uno): вхідні сигнали (кнопки, limit switches, датчики), локальне керування (relay, LED, PWM), UART CLI і JSON-протокол, I2C-периферія, persistent storage, watchdog / recovery, Wi-Fi / MQTT (симуляція), offline buffer. Кожен Task тестував окрему збірку; разом вони покривають компоненти продукту.

Версії FW / HW: назви збірок і banner (v2.0, homework_buggy, BUGGY); ELF SHA256 `1e9f6d28d20fb872` зафіксовано лише для Task 5. Детальний огляд — розділ 2 [master-test-plan.md](master-test-plan.md).

## Test strategy

Шість критичних ризиків R1–R6: неправильна команда керування, датчик недоступний, зависання прошивки, втрата живлення під час збереження, мережа недоступна, деградація пам'яті. Test Matrix із 22 тестів (9 × P1, 8 × P2, 5 × P3), рівні: component / interface checks, system black-box, fault injection, non-functional / reliability, automation / regression. Критерії успіху — Exit Criteria у [master-test-plan.md](master-test-plan.md) (розділ 12). Матриці: [Risk_Matrix_UA.md](Risk_Matrix_UA.md), [Test_Matrix_UA.md](Test_Matrix_UA.md).

## Environment & tools

Wokwi 3.7.0, Wokwi CLI v0.27.1, PlatformIO IDE 3.3.2, logic analyzer (sigrok / PulseView), Python 3.9.12, pytest 8.4.2, pyserial (RFC2217), симульований MQTT broker. Хост: macOS 12, MacBook Pro mid-2015, Chrome 150, VS Code 1.136. Real hardware не використовувалось.

## Key scenarios

1. Реверс воріт без safe stop → обидва relay HIGH (Task 1).
2. Sweep імпульсу NOISE 0.5–30 мс → поріг debounce 1–2 мс замість ≈30 мс (Task 2).
3. UART-рядок із 41 символу → SYSTEM FAULT і reboot (Task 3).
4. I2C NACK → 33.09 с тиші на шині (Task 4).
5. Powerloss під час save → counter 8 → 108 (Task 5).
6. RESET відповідає OK, але LED / PWM не змінюються; GET TEMP — invalid JSON (Task 6).
7. Offline buffer: SEND ×12 → 24 publish, втрачені ID, heap −23.2% (Task 7).

## Bugs / findings

| Task | Проєкт | README проєкту | Defects | Severity як зафіксовано |
|---|---|---|---|---|
| 1 | Smart Gate Controller | [wokwi/task1_gate/](wokwi/task1_gate/README.md) | 12 | 5 Blocker, 3 Major, 3 Minor, 1 «Intermittent» |
| 2 | Button Debounce | [wokwi/task2_debounce/](wokwi/task2_debounce/README.md) | 1 | 1 Major |
| 3 | UART CLI | [wokwi/task3_uart_cli/](wokwi/task3_uart_cli/README.md) | 5 | 1 Critical, 4 Major |
| 4 | I2C sensor polling | [pulseview/task4_i2c/](pulseview/task4_i2c/README.md) | 2 | 2 High |
| 5 | Recovery / Fault Injection | [pytest/task5_recovery/](pytest/task5_recovery/README.md) | 5 | 3 Major (High), 2 Medium |
| 6 | JSON serial protocol | [pytest/task6_protocol/](pytest/task6_protocol/README.md) | 4 | 2 High, 1 Medium, 1 Low / Medium |
| 7 | IoT network / memory | [network-stress/task7_network_memory/](network-stress/task7_network_memory/README.md) | 7 | 3 Critical, 2 Major, 1 Minor, 1 Trivial |

Повний реєстр із Expected / Actual — [bug-reports/BUG_REGISTER_UA.md](bug-reports/BUG_REGISTER_UA.md). Найважливіше: перекриття relay (T1-06, T1-09), crash від довгого рядка (T3-05), counter +100 після powerloss (T5-01), overflow, дублікати й витік heap (T7-03…05).

## Evidence

Логи, trace I2C, pytest-звіти, метрики heap і мережі, bug reports — у папках проєктів; повний індекс із командами перевірки — [EVIDENCE_INDEX_UA.md](EVIDENCE_INDEX_UA.md). Основне:
- логи: `wokwi/*/logs/`, `pytest/*/logs/`, `network-stress/*/logs/`;
- I2C trace: [pulseview/task4_i2c/i2c_failure.sr](pulseview/task4_i2c/i2c_failure.sr);
- метрики: [network-stress/network_stress.csv](network-stress/network_stress.csv), [heap trend](network-stress/task7_network_memory/screenshots/task7_heap_trend.png);
- pytest: [Task 6](pytest/task6_protocol/pytest_output.txt), [Task 5](pytest/task5_recovery/pytest_log_task5.pdf), [Task 7](network-stress/task7_network_memory/);
- підсумок тестів: [test_summary.md](test_summary.md).

Прогалини: немає скріншотів вікна Wokwi, відео та файлів проєкту Wokwi (diagram.json); у підпапках `screenshots/` лежать PNG-рендери PDF-експортів terminal і графік heap; SPI не тестувався; test_*.py Tasks 5 і 6 відсутні в архіві.

## What I learned / decisions made

- Ризик визначає глибину тестів: шість ризиків зі score 9 тестувалися першими й із повторами від 4/5 до 26/26.
- Severity і reproducibility — різні поля (урок із T1-07, де «Intermittent» записано як severity).
- Пороги без вимог (debounce, latency PING, I2C recovery) я позначив як припущення й виніс в open questions.
- Failed pytest ≠ firmware bug: причину доводив ланцюжком test logic → environment → communication → requirement → firmware.
- Рішення: **NO-GO**; переоцінка — після виправлення Blocker / Critical і High defects, retest і прогону на real hardware ([Release_Decision_UA.md](Release_Decision_UA.md), [QA_Conclusion_UA.md](QA_Conclusion_UA.md)).
- Наступні кроки: Wokwi-скріншоти й відео, повторний Task 4 із FAULT off, перевірка Task 5 за часом firmware, автоматизація Tasks 1 і 4.

## Структура репозиторію

```
embedded-qa-portfolio/
├── README.md                    опис проєкту, цілі, підхід, як користуватись
├── master-test-plan.md          повний план тестування, критерії, покриття
├── wokwi/                       симуляції схем, проєкти та конфігурації Wokwi (Tasks 1, 2, 3)
├── pulseview/                   захоплення та аналіз сигналів (Task 4)
├── pytest/                      автотести на Python (Tasks 5, 6, 7)
├── network-stress/              сценарії стрес-тестів мережі та результати (Task 7)
├── bug-reports/                 звіти про знайдені дефекти та відтворення (Tasks 1–7)
└── resume/                      резюме та профільні матеріали
```

Додатково в корені: [case_study_UA.md](case_study_UA.md) (Case Study), [Risk_Matrix_UA.md](Risk_Matrix_UA.md), [Test_Matrix_UA.md](Test_Matrix_UA.md), [Release_Decision_UA.md](Release_Decision_UA.md), [QA_Conclusion_UA.md](QA_Conclusion_UA.md), [EVIDENCE_INDEX_UA.md](EVIDENCE_INDEX_UA.md), [test_summary.md](test_summary.md).

## Як користуватись

1. Почніть із цього README, потім [master-test-plan.md](master-test-plan.md).
2. Для кожного висновку відкрийте evidence за [EVIDENCE_INDEX_UA.md](EVIDENCE_INDEX_UA.md): там є conclusion і команда перевірки.
3. Деталі проєкту — у README відповідної папки (таблиця «Bugs / findings»).
