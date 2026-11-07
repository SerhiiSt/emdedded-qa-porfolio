# Task 7 — IoT network / memory stability (network stress)

## Project goal

Перевірити поведінку IoT-вузла при втраті мережі та під навантаженням: reconnect, offline buffer, flush, дублікати, стабільність heap (R1–R8).

## System under test

ESP32 + DHT22 із симульованим MQTT broker; збірка «homework_buggy». Стани DISCONNECTED / BACKOFF / CONNECTING / CONNECTED, offline buffer (capacity 8, DROP_OLDEST), команди NET DOWN, NET UP, SEND, STRESS n, STATS.

## Test strategy

Risk-based: QR-05, QR-06 (score 9, P1) і QR-11 (score 4, P3). Network stress, boundary, memory stability, ідентифікація повідомлень за ID. Тести: TM-09, TM-10, TM-11, TM-20, TM-21.

## Environment & tools

Wokwi CLI v0.27.1, PlatformIO device monitor, Python 3.9.12, pytest 8.4.2, pyserial; тести — у [pytest/task7_network_memory/tests/](../../pytest/task7_network_memory/tests/).

## Key scenarios

1. NET DOWN 20 с: 391 retry (backoff 500 мс один раз, далі 50 мс) замість ≤12.
2. NET DOWN → SEND ×12: buffer=12, dropped=0 замість buffer=8, dropped=4.
3. NET UP: 24 publish для 12 повідомлень, ID 11–14 втрачено.
4. 10 × STRESS 100: heap 344 924 → 264 920 B (−80 004 B, −23.2%).
5. STRESS −5 / 1.5 / abc: тихо виконується як count=1.

## Bugs / findings

Severity як зафіксовано в Task: 3 Critical, 2 Major, 1 Minor, 1 Trivial. Усього defects: 7.

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T7-01 | Reconnect storm, приблизно 19 retry на секунду | Major / Medium | 5/5 | Не більше 12 retry за 20 с, зростаючий backoff (R2) | 391 retry за 20 с, backoff 500 мс один раз, далі 50 мс |
| T7-02 | Кожне буферизоване повідомлення публікується двічі після NET UP | Major / Medium | 6/6 | Кожен ID один раз, duplicates=0 (R6) | Кожен ID двічі (12 повідомлень → 24 publish) |
| T7-03 | Buffer росте понад capacity 8, нічого не відкидається | Critical / High | 4/4 | buffer=8, dropped=4 для 12 повідомлень (R4) | buffer=12, dropped=0 |
| T7-04 | Витік heap, 80 B на повідомлення | Critical / High | 5/5 | Втрата heap менша за 5% (R7) | −80 004 B (−23.2%) за 10 × STRESS 100 |
| T7-05 | Flush після overflow губить найстаріші повідомлення й повторює інші | Critical / High | 4/4 | 8 найновіших ID по одному разу, від найстарішого | 24 publish; ID 19–22 чотири рази, 15–18 двічі, ID 11–14 не опубліковано |
| T7-06 | Некоректні аргументи STRESS мовчки виконуються як count=1 | Minor / Low | 2 запуски | «[CLI] ERROR» (R2, R8) | Виконується з count=1 без помилки |
| T7-07 | Fault-команди не є idempotent | Trivial / Low | 2 запуски | Повторна команда у тому ж стані нічого не змінює (R1, R8) | Повторний NET DOWN знову входить у DISCONNECTED, retry зростає |

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [../network_stress.csv](../network_stress.csv) — 166 рядків зі STATUS-логів (net, buffer, sent, dropped, duplicates, heap)
- [logs/](logs/) — 6 device-monitor логів, ключовий [device-monitor-261024-174403.log](logs/device-monitor-261024-174403.log)
- [screenshots/task7_heap_trend.png](screenshots/task7_heap_trend.png) — графік heap із логів; [state model](screenshots/task7_test_sheet_p3_state_model.png)
- [IoT_Network_Memory_Test_Sheet_Webinar_7_UA.pdf](IoT_Network_Memory_Test_Sheet_Webinar_7_UA.pdf), [report.html](report.html), [manual_task7_log.pdf](manual_task7_log.pdf), [test_iot_recommendations_log.pdf](test_iot_recommendations_log.pdf), [platformio-device-monitor.pdf](platformio-device-monitor.pdf)
- Результати pytest: manual scenarios — 5 failed, 16 passed, 1 skipped (264.84 с); recommendations — 22 failed, 5 passed (520.01 с)

Прогалини: long outage (TC-27) пропущено; TC-15 провалився через помилку тесту, а не defect.

## What I learned / decisions made

- Лічильник duplicates розходиться з реальним логом (12 проти 16 повторів): метрики пристрою теж треба перевіряти.
- ID повідомлень — найпростіший спосіб довести втрату й дублювання.
- Тренд heap потрібно дивитись на серії прогонів, одиничний замір нічого не доводить.
- Рішення: залишити STRESS 100 × 10 у smoke-наборі регресії.
