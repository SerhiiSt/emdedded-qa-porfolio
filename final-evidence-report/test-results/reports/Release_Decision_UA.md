# Release Decision — Embedded QA (Tasks 1–7)

Рішення про готовність до release семи firmware-збірок Smart IoT Safety Controller. Підготував Serhii, QA Embedded Engineer, 2026-11-01. Рекомендація QA-інженера на основі evidence з Tasks 1–7.

Пов'язані документи: [master-test-plan.md](../../master-test-plan.md) (розділи 12, 16, 17) · [QA_Conclusion_UA.md](QA_Conclusion_UA.md) · [Risk_Matrix_UA.md](Risk_Matrix_UA.md) · [Test_Matrix_UA.md](Test_Matrix_UA.md) · [EVIDENCE_INDEX_UA.md](EVIDENCE_INDEX_UA.md) · [test_summary.md](test_summary.md)

## 1. Рішення

| | |
|---|---|
| **Рішення** | **NO-GO** |
| Обсяг | 7 збірок: Smart Gate Controller, Button Debounce, UART CLI, I2C sensor polling, Recovery / Fault Injection, JSON serial protocol, IoT network / memory |
| Підстава | Exit Criteria не виконані; 36 відкритих defects, з них 9 Blocker / Critical |
| Статус ризиків | Known Risk (GO WITH RISKS) не обґрунтований: відкриті ризики стосуються safety, data integrity і стабільності |
| Наступна переоцінка | Після виправлення й retest Blocker / Critical та High defects і прогону ключових тестів на real hardware |

Логіка рішення (Від доказів до рішення): вимога / ризик → тестування пріоритетних ризиків → докази (логи, trace, звіти, метрики) → знахідки → рішення. Для цього проєкту всі шість критичних ризиків R1–R6 підтверджені дефектами, тож результат — **No-Go**: критерії не виконані, release неможливий без виправлень.

## 2. Перевірка Exit Criteria

| Exit Criteria | Умова | Фактичний стан | Виконано |
|---|---|---|---|
| Critical scenarios виконані | Усі критичні сценарії протестовані й працюють | Виконані, але не працюють як очікується (9 Blocker / Critical) | ✖ |
| Немає відкритих Blocker / Critical | Blocker = 0, Critical = 0 | Blocker 5 (Task 1), Critical 4 (Task 3: 1, Task 7: 3) | ✖ |
| Regression пройдений | 100% після змін | Не виконувався: виправлень ще немає | ✖ |
| Recovery scenarios підтверджені | Перезавантаження, втрата живлення, втрата зв'язку, збій прошивки, пошкодження даних | Powerloss (T5-01), watchdog (T5-03), NACK (T4-01), мережа (T7-05) провалені | ✖ |
| Evidence збережений | Звіти, логи, скріншоти, вимірювання, відео доступні | Логи, traces, звіти — так; Wokwi-скріншоти й відео — ні | Частково |
| Known risks прийняті або задокументовані | Ризики оцінені й прийняті командою або задокументовані | Задокументовані ([master-test-plan.md](../../master-test-plan.md), розділ 16); не прийняті | Частково |

Результат: 0 із 6 критеріїв виконано повністю, 2 — частково.

## 3. Defects, що блокують release (Blocker / Critical)

| Defect | Task | Severity | Вплив | Evidence |
|---|---|---|---|---|
| T1-02 | 1 Gate | Blocker | OPEN limit не переводить ворота в OPEN; relay лишається ON | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| T1-03 | 1 Gate | Blocker | Стан OPEN недосяжний, R15 неможливо перевірити | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| T1-06 | 1 Gate | Blocker | Реверс напрямку без safe stop | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| T1-09 | 1 Gate | Blocker | Обидва relay короткочасно активні (4/5 запусків): ризик пошкодження драйвера мотора | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| T1-11 | 1 Gate | Blocker | RESET не очищає цикл limit switch; допомагає лише power cycle | [Bug_Report xlsx](../../test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx) |
| T3-05 | 3 UART CLI | Critical | Рядок довший за 40 символів → SYSTEM FAULT і reboot (26 з 26) | [TC-27.log](../../logs/task3_uart_cli/TC-27.log) |
| T7-03 | 7 IoT network | Critical | Buffer росте понад capacity 8, нічого не відкидається | [device-monitor log](../../logs/task7_network_memory/device-monitor-261024-174403.log) |
| T7-04 | 7 IoT network | Critical | Витік heap 80 B на повідомлення, −23.2% за 1000 повідомлень | [heap trend](../../screenshots/task7_heap_trend.png), [network_stress.csv](../../logs/network_stress.csv) |
| T7-05 | 7 IoT network | Critical | Flush після overflow губить найстаріші повідомлення й повторює інші | [device-monitor log](../../logs/task7_network_memory/device-monitor-261024-174403.log) |

Окрім них, High / Major defects теж впливають на рішення: T5-01 (counter +100 після powerloss без повідомлення), T6-02 і T6-03 (RESET не скидає, invalid JSON), T4-01 (I2C мовчить 33.09 с), T5-02, T5-03 (таймінги recovery).

## 4. Рішення за проєктами

| Task | Збірка | Verdict | Головна причина | Умова для повторної оцінки |
|---|---|---|---|---|
| 1 | Smart Gate Controller | **NO-GO** | 5 Blocker: relay перекриваються, OPEN недосяжний, RESET не відновлює | TM-01…04 пройдені 20 / 20, relay ніколи не HIGH разом |
| 2 | Button Debounce | **NO-GO** | T2-01: імпульси від 2 мс приймаються як натискання | TM-12, 13 пройдені; погоджений поріг debounce |
| 3 | UART CLI | **NO-GO** | Critical T3-05 + чотири Major у валідації | TM-06 (41+ символів без reboot), TM-07 |
| 4 | I2C sensor polling | **NO-GO** | T4-01: тиша на шині після NACK; recovery не підтверджено | TM-14 із FAULT off у відомий момент; вимога до I2C recovery |
| 5 | Recovery / Fault Injection | **NO-GO** | T5-01 (дані), T5-02, T5-03 (таймінги) | TM-08, 17, 18 за часом firmware |
| 6 | JSON serial protocol | **NO-GO** | T6-02, T6-03: контракт протоколу порушено | TM-15; погоджений ліміт latency PING |
| 7 | IoT network / memory | **NO-GO** | 3 Critical: buffer, heap, flush | TM-09, 10, 11 пройдені, heap −5% або менше |

## 5. Чому не Known Risk (GO WITH RISKS)

- Відкриті дефекти — не обмеження продуктивності чи тимчасові обмеження стенда, а порушення **safety** (T1-06, T1-09), **data integrity** (T5-01, T7-05), **стабільності** (T3-05, T7-04) і **коректності протоколу** (T6-02, T6-03).
- Для Known Risk потрібні прийняті ризики з планом моніторингу; такого плану для безпекових дефектів воріт і втрати даних немає.
- Виправлення ще не вносилися, тож неможливо довести, що defects, які зараз приховують інші (T1-03 ховає R15), не мають наслідків.
- Усі результати — з симуляторів; електричні ефекти (relay timing, brown-out) не підтверджені, тож залишковий ризик після виправлень теж невідомий.

## 6. Умови для Go (повторна оцінка)

1. Усі 9 Blocker / Critical виправлені й пройшли retest у всіх повторах (мінімум 3/3; для TM-01 — 20 / 20).
2. High defects (T4-01, T5-01, T6-02, T6-03 та інші) виправлені або мають письмовий waiver власника продукту.
3. Regression: P1-набір (TM-01, 02, 03, 04, 06, 08, 09, 10, 11) і smoke на кожній збірці — 100% passed.
4. Recovery підтверджено: powerloss, watchdog (5 с ±15%), NACK, NET DOWN / UP.
5. Метрики: heap −5% або краще після 10 × STRESS 100; не більше 12 retry за 20 с; duplicates = 0.
6. Ключові тести TM-01, TM-08, TM-14 повторені на real hardware (TM-22).
7. Open questions закриті: поріг debounce, PWM-одиниці, LED / PWM, latency PING, поведінка I2C recovery.
8. Evidence доповнено: Wokwi-скріншоти, відео, файли проєкту Wokwi.

## 7. Known risks (документовані, не прийняті)

| Ризик | Статус | План |
|---|---|---|
| Результати лише з симуляторів | Задокументовано | Real hardware gate |
| Task 4 — один capture | Задокументовано | Повторити з FAULT off |
| Таймінги Task 5 з simulator clock | Задокументовано | Перемірити за часом firmware |
| Пороги без вимог (debounce, latency PING, I2C recovery) | Open questions | Погодити з власником вимог |
| Не протестовано: стан relay після watchdog reset, збій DHT22, long outage, SPI | Задокументовано | Додати в наступний цикл |

## 8. Хто приймає рішення

| Роль | Відповідальність | Статус |
|---|---|---|
| QA-інженер (Serhii) | Рекомендація на основі evidence | **NO-GO** (2026-11-01) |
| Product owner | Остаточне рішення про release | Очікується |
| Test manager | Підтвердження критеріїв і evidence | Очікується |
| QA команда / інші стейкхолдери | Перегляд ризиків і плану виправлень | Очікується |

У навчальному кейсі рішення ухвалює ментор / techlead; ця рекомендація — підстава для нього.

## 9. Пріоритетний план виправлень

| Пріоритет | Дія | Defects | Risk |
|---|---|---|---|
| 1 | Interlock relay, safe stop при реверсі | T1-06, T1-09 | R1 |
| 2 | Досягнення OPEN і recovery після limit / timeout | T1-01, T1-02, T1-03, T1-07, T1-11 | R1 |
| 3 | Обмеження довжини рядка (reboot) і валідація CLI | T3-05, T3-01…04 | R1, R3 |
| 4 | Цілісність persistent counter при powerloss | T5-01 | R4 |
| 5 | Buffer, flush і витік heap | T7-03, T7-04, T7-05, T7-02 | R5, R6 |
| 6 | Контракт JSON-протоколу | T6-02, T6-03, T6-01 | R1 |
| 7 | Recovery і таймінги | T4-01, T5-02, T5-03, T5-05 | R2, R3 |
| 8 | Debounce, backoff, діагностика, відкриті питання | T2-01, T7-01, T1-04, T1-05, T1-08, T1-12, T7-06, T7-07 | R1, R5 |
