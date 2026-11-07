# Master Test Plan — Embedded QA (Tasks 1–7)

Smart IoT Safety Controller: сім симульованих embedded/IoT збірок · Serhii, QA Embedded Engineer · 2026-11-01

Master Test Plan пов'язує продукт, ризики, методи, evidence та критерії готовності. Цей документ відповідає структурі з вебінару 8 (8 блоків) і шаблону курсу (17 розділів). Evidence зібрано в цьому ж пакеті (`final-report/`); повний реєстр defects — у розділі «Appendix A».

## 0. Що таке цей план (відповіді на 7 питань Master Test Plan)

| Питання | Відповідь | Розділ |
|---|---|---|
| ЩО тестуємо? | Firmware семи збірок: ворота (Arduino Uno), debounce, UART CLI, I2C, recovery / fault injection, JSON-протокол, IoT network / memory | 2, 4 |
| НАВІЩО тестуємо? | Підтримати рішення про release: чи безпечні, відновлювані й стабільні ці збірки | 1, 3 |
| ЯК тестуємо? | Risk-based testing, black-box, fault injection, pytest / Wokwi CLI автоматизація | 7, 8, 9, 13 |
| ДЕ тестуємо? | Wokwi, Serial / CLI, logic analyzer + PulseView, Python + pytest, MQTT / network model; real hardware — наступний gate | 10 |
| КОЛИ зупиняємо тестування? | Exit Criteria: немає відкритих Blocker / Critical, regression пройдено, recovery підтверджено, evidence збережено | 12 |
| ЯКИЙ evidence потрібен для рішення про готовність? | Логи, traces, pytest-звіти, метрики heap, bug reports, test summary | 14 |
| ХТО приймає рішення? | Product owner та test manager; QA-інженер дає рекомендацію (у навчальному кейсі рішення ухвалює ментор / techlead) | 17 |

## 1. Document Purpose

План описує продукт, межі, ризики, стратегію й Exit Criteria для семи embedded-пристроїв і підтримує одне рішення: чи можна випускати ці збірки, і що виправити та повторно перевірити першим. За результатами Tasks 1–7 відповідь — **NO-GO** (розділ 17).

## 2. System Overview

Пристрій: Smart IoT Safety Controller — MCU-контролер (ESP32; у Task 1 — Arduino Uno), який збирає дані датчиків і входів, локально керує relay / LED / PWM, спілкується по UART і мережі (Wi-Fi / MQTT), зберігає критичні дані й відновлюється після збоїв. Кожен Task тестував окрему збірку; разом вони покривають компоненти продукту (не один інтегрований пристрій).

| Task | Збірка | Hardware (симульований) | Firmware: що перевіряється | Інтерфейси |
|---|---|---|---|---|
| 1 | Smart Gate Controller | Arduino Uno, 2 relay (pin 8 open, pin 9 close), limit switches, 3 кнопки, LED | State machine CLOSED / OPENING / OPEN / CLOSING / STOPPED / ERROR, timeout 10 с, R1–R16 | Serial O, C, S, RESET; кнопки; limit-входи |
| 2 | Button Debounce | ESP32, BUTTON, NOISE, LED | Одна logical event і одна action на натискання, watchdog | GPIO interrupts, Serial Logger |
| 3 | UART CLI Homework Device v2.0 | ESP32 | help, status, set speed, set timeout, led; CONFIG SAVED / DIRTY; ліміт 40 символів; REQ-01…16 | UART console |
| 4 | I2C sensor polling | ESP32 + MPU-6050 | Опитування 0x68 кожні ≈1.001 с, init 0x6B, перемикач FAULT | I2C, capture logic analyzer |
| 5 | Recovery / Fault Injection («homework_buggy») | ESP32 DevKit V1, relay, DHT22 | Deep sleep, task watchdog 4000 мс, persistent counter, powerloss | Serial sleep, hang, powerloss, status |
| 6 | JSON serial protocol (BUGGY) | ESP32, LED, PWM, датчик температури | PING, STATUS, GET TEMP, SET LED, SET PWM 0–100, RESET | UART, одна JSON-відповідь на команду |
| 7 | IoT network / memory stability («homework_buggy») | ESP32 + DHT22, симульований MQTT broker | Reconnect + backoff, offline buffer (capacity 8, DROP_OLDEST), STRESS n, R1–R8 | Serial NET DOWN / NET UP / SEND / STRESS / STATS, MQTT publish log |

**Inputs:** кнопки (Tasks 1, 2), limit switches / перемикач FAULT / джерело NOISE (Tasks 1, 2, 4), датчики DHT22, MPU-6050 та датчик температури (Tasks 4–7), живлення (powerloss, Task 5).
**Outputs:** LED (Tasks 1, 2, 6), relay (Tasks 1, 5), PWM (Task 6), відповіді по UART, MQTT publish (Task 7). Зумер і дисплей у збірках не використовуються.
**Interfaces:** GPIO, UART, I2C, симульовані Wi-Fi і MQTT; SPI не тестувався.
**Критичні стани:** OPENING / CLOSING / ERROR (Task 1), стан після RESET (Task 6), CONFIG DIRTY / SAVED (Task 3), збереження counter і reset reason (Task 5), шина I2C після NACK (Task 4), DISCONNECTED / BACKOFF / CONNECTING / CONNECTED, повний buffer і мала heap (Task 7).
**Зовнішні залежності:** живлення (powerloss injection, brown-out не перевірявся), мережа / Wi-Fi та MQTT broker (симуляція), периферія MPU-6050 / DHT22 (симуляція), інструменти (Wokwi, Wokwi CLI, pytest, logic analyzer); мобільний застосунок і хмара — поза збірками.

## 3. Quality Objectives

1. **Safety:** два relay напрямку ніколи не активні разом; ворота завжди приходять у визначений стан.
2. **Functional correctness:** кожна вимога (R / REQ / AC) виконується за специфікацією.
3. **Robustness:** некоректний, надто довгий чи шумний вхід відхиляється без crash і без тихої зміни стану.
4. **Recoverability:** watchdog, sleep і powerloss повертають валідний стан за вказаний час.
5. **Data integrity:** збережені значення лишаються валідними після перерваного збереження.
6. **Network resilience:** обмежені retry, кожне повідомлення надсилається один раз, втрати фіксуються.
7. **Memory stability:** втрата heap менша за 5% під час stress-прогону.
8. **Observability:** кожен збій видно в log, trace чи status.

## 4. Scope (що тестуємо)

Чіткий scope захищає команду від нескінченного розширення тестів. IN SCOPE — перевірка firmware, інтерфейсів, протоколів, сценаріїв і критичних станів.

| Група | Що входить | Покриття в Tasks 1–7 | Прогалини |
|---|---|---|---|
| Firmware | Логіка пристрою, обробка подій, таймери, стани, функціональні вимоги | State machine воріт (T1), debounce (T2), CLI-стан і конфігурація (T3), sleep / watchdog / counter (T5), reconnect і buffer (T7) | Версії збірок зафіксовано не скрізь (ELF SHA256 лише в Task 5) |
| Інтерфейси | GPIO, UART, I2C, SPI, Wi-Fi, MQTT | GPIO (T1, T2, T5, T6), UART (T3, T5, T6, T7), I2C (T4), MQTT і мережа — симульовані (T7) | SPI не тестувався; реальний Wi-Fi не тестувався |
| Протоколи | Формати повідомлень, обмін даними, обробка помилок, timeouts | UART CLI і граматика команд (T3), JSON-протокол (T6), I2C ACK / NACK (T4), MQTT publish (T7) | I2C recovery і latency PING без формальних вимог |
| Сценарії | Функціональні сценарії, послідовності дій, граничні випадки | Реверс воріт, sweep імпульсів 0.5–30 мс, довжина рядка 40 / 41 / 200 / 1000, SET PWM 0–101, SEND ×8 / ×9 / ×12 | Integration-сценарії між збірками не виконувалися |
| Критичні стани | Відновлення після збоїв, втрата зв'язку, некоректні вхідні дані, перезавантаження | Powerloss під час save, hang → watchdog, NET DOWN / UP, NACK, одночасні limit switches | Реальний brown-out; стан relay після watchdog reset (тест `test_actuator_off_after_wdt` завершився ERROR); DHT22 failure |

## 5. Out of Scope (що не тестуємо)

| Група | Що не тестуємо | Чому |
|---|---|---|
| Залізо (Hardware) | Схемотехніка, компоненти, пайка, апаратні дефекти, електричні характеристики | Тестувалися симулятори; contact bounce — атрибут симуляції |
| Механіка | Корпус, кріплення, кнопки, конектори, вібрації, навантаження на мотор воріт | Немає фізичної моделі |
| Дизайн / UI | Зовнішній вигляд, макети, графіка, UX | Пристрої без UI; взаємодія лише через serial |
| Застосунки верхнього рівня | Мобільні / web-додатки, хмарні панелі | Не є частиною вимог до прошивки |
| Сторонні сервіси | Реальний MQTT broker, TLS, автентифікація, хмарні API | Мережа змодельована (NET DOWN / NET UP); security не входить у вимоги |
| Інше | Security-fuzzing, довготривалий soak (TC-24 300 с, TC-27 long outage), енергоспоживання в deep sleep, ручний TC-25 | Не завершено, пропущено або неможливо виміряти в симуляторі |

**Переваги чіткого scope:** фокус на важливому; захист від endless-розширення тестів; прозорість для команди та стейкхолдерів; ефективне планування й оцінка обсягу.

## 6. Assumptions / Constraints

- Wokwi 3.7.0 + PlatformIO IDE 3.3.2 (Task 1); Wokwi CLI v0.27.1 (Tasks 2–7); Python 3.9.12, pytest 8.4.2, pyserial через RFC2217 (Tasks 5–7). Хост: macOS 12, MacBook Pro mid-2015.
- Час — з simulator clock, а не з firmware.
- Task 4: один capture logic analyzer (610 транзакцій, 642.21 с) без serial log.
- Пороги, які є припущеннями тестувальника: debounce ≈ 30 мс (Task 2), не більше 12 retry за 20 с і втрата heap менша за 5% (Task 7), допуск wake-up ±15% (Task 5).
- Для I2C recovery (Task 4) і latency PING (Task 6) вимог немає; очікування вважалися неявними.
- Шкали severity різні в різних Tasks (розділ 15).
- Тестові дані та облікові записи не потрібні: усі збірки керуються через serial / scenario.

## 7. Quality Risks

### 7.1 Критичні ризики R1–R6 (Крок 1 вебінару)

| R | Критичний ризик | Відповідні QR | Task | Score (P × I) | Evidence | Статус |
|---|---|---|---|---|---|---|
| R1 | Неправильна команда керування | QR-01, QR-02, QR-09 | 1, 3, 6 | 9 / 9 / 6 | Реверс без safe stop і перекриття relay (T1-06, T1-09); RESET не скидає LED / PWM (T6-02); невалідні значення приймаються (T3-01…04) | Дефекти підтверджено |
| R2 | Датчик недоступний | QR-08 | 4 | 6 | I2C NACK на 0x69 і 33.09 с тиші, `test-results/i2c_failure.sr` | Підтверджено; DHT22 failure не тестувався |
| R3 | Зависання прошивки | QR-03, QR-10 | 3, 5 | 9 / 6 | Crash при рядку понад 40 символів (T3-05); watchdog через 14.59 с замість 5 с (T5-03) | Дефекти підтверджено |
| R4 | Втрата живлення під час збереження | QR-04 | 5 | 9 | Counter 8 → 108 після powerloss (T5-01) | Дефект підтверджено |
| R5 | Мережа недоступна | QR-05, QR-11 | 7 | 9 / 4 | Overflow без drop, дублікати й втрата ID, reconnect storm (T7-01, 02, 03, 05) | Дефекти підтверджено |
| R6 | Деградація пам'яті | QR-06 | 7 | 9 | Heap −80 004 B (−23.2%) за 10 × STRESS 100 (T7-04), `screenshots/task7_heap_trend.png` | Дефект підтверджено |

Score = Probability × Impact за шкалою 1–3 (High 7–9, Medium 4–6, Low 1–3); повна матриця — `test-results/reports/Risk_Matrix_UA.md`. Нумерація R1–R6 — з вебінару; `EVIDENCE_INDEX_UA.md` використовує R01–R08 із шаблону курсу (відповідність у розділі 14a).

### 7.2 Повний реєстр Quality Risks

| Risk ID | Risk | Justification | Impact | Probability | Priority | Mitigation / Test |
|---|---|---|---|---|---|---|
| QR-01 | Обидва relay воріт вмикаються одночасно при реверсі | Реверс без safe stop у 5/5 запусків, перекриття relay у 4/5; може пошкодити драйвер мотора | Critical (3) | High (3) | P1 | TM-01 |
| QR-02 | Ворота не досягають OPEN, помилки не очищаються через RESET | OPEN не досягнуто в 5/5 запусків; цикл limit switch переживає RESET | Critical (3) | High (3) | P1 | TM-02, 03, 04, 05 |
| QR-03 | Надто довгий UART-ввід валить і перезавантажує пристрій | 26 з 26 спроб понад 40 символів | Critical (3) | High (3) | P1 | TM-06, 07 |
| QR-04 | Перерване збереження пошкоджує persistent counter (+100) | Counter зростав рівно на 100 після кожного powerloss, нічого не логувалося | High (3) | High (3) | P1 | TM-08 |
| QR-05 | Повідомлення губляться або дублюються після offline-періоду | Overflow нічого не відкинув, flush повторював і губив ID | Critical (3) | High (3) | P1 | TM-09, 10 |
| QR-06 | Витік heap 80 B на повідомлення | −23.2% за 1000 повідомлень; out of memory приблизно після 4300 | Critical (3) | High (3) | P1 | TM-11 |
| QR-07 | Шумові імпульси від 2 мс приймаються як натискання | Кожен імпульс від 2 мс ставав logical event і action | High (2) | High (3) | P2 | TM-12, 13 |
| QR-08 | Пристрій мовчить на I2C після першого NACK | 33 с без опитування й без повідомлення про помилку | High (3) | Medium (2) | P2 | TM-14 |
| QR-09 | Порушено контракт протоколу | RESET відповідає OK, але LED / PWM не змінюються; GET TEMP без закривної дужки | High (2) | High (3) | P2 | TM-15, 16 |
| QR-10 | Збої таймінгу: wake-up, watchdog, 60-секундний sleep | Wake-up 0.4–0.7 с незалежно від N; watchdog 14.6 с замість 5 с | High (2) | High (3) | P2 | TM-17, 18, 19 |
| QR-11 | Reconnect storm: ≈19 retry на секунду | 391 retry за 20 с із фіксованим backoff 50 мс | Medium (2) | Medium (2) | P3 | TM-20, 21 |
| QR-12 | Прогалини у вимогах і обмеження симулятора | Пороги — припущення, результати симульовані | Medium (2) | Medium (2) | P3 | TM-22 |

### 7.3 Risk-Based Testing

Ризик = Імовірність × Вплив: High (7–9) тестуємо спочатку й глибше, ризики переглядаємо на кожному етапі проєкту. Підсумок: 6 ризиків зі score 9 (QR-01…06), 4 зі score 6 (QR-07…10), 2 зі score 4 (QR-11, 12).

## 7a. Test Matrix (Матриця тестування)

Окремий файл із повною матрицею, фактичними результатами та посиланнями на evidence: [Test_Matrix_UA.md](test-results/reports/Test_Matrix_UA.md).

### Крок 2 — матриця «Ризик → Тип тестування → Докази»

| R | Ризик | Тип тестування | Докази тестування |
|---|---|---|---|
| R1 | Некоректний вхід / неправильна команда | Граничні значення / негативні сценарії | Serial log + pytest (`logs/task3_uart_cli/`, `test-results/task6_protocol/pytest_output.txt`) |
| R2 | Датчик недоступний | Fault Injection (перемикач FAULT) | Trace I2C (`test-results/i2c_failure.sr`) |
| R3 | Зависання прошивки | Recovery | Log перезапуску watchdog (`logs/task5_recovery/serial_20261014_152215.log`) |
| R4 | Втрата живлення | Reliability | Counter до / після (`logs/task5_recovery/`), валідація даних |
| R5 | Збій мережі | Стрес-тест / recovery | Лог MQTT і message ID (`logs/task7_network_memory/`, `logs/network_stress.csv`) |
| R6 | Деградація пам'яті | Memory stability | Heap-метрики (`screenshots/task7_heap_trend.png`, `logs/network_stress.csv`) |

### Повна Test Matrix (22 тести)

Priority: P1 = release blocker, P2 = має пройти або мати waiver, P3 = до наступного milestone.

| Test ID | Risk / defects | Test Objective | Test Type | Test Level | Priority | Expected Result |
|---|---|---|---|---|---|---|
| TM-01 | QR-01 · T1-06, T1-09 | Relay не вмикаються одночасно при реверсі (O під час CLOSING, C під час OPENING) | Functional (safety) | System | P1 | CLOSING → STOPPED → OPENING; relayOpen (pin 8) і relayClose (pin 9) ніколи не HIGH в одному циклі, 20 з 20 реверсів (R4, R8) |
| TM-02 | QR-02 · T1-01 | Movement timeout 10 с в обох напрямках | Functional | System | P1 | «ERROR: movement timeout», стан → ERROR, обидва relay OFF (R9) |
| TM-03 | QR-02 · T1-02, T1-03 | OPEN limit і стан OPEN | Functional | System | P1 | LIMIT_OPEN → стан OPEN, relay OFF; C з OPEN запускає CLOSING (R6, R15) |
| TM-04 | QR-02 · T1-07, T1-10, T1-11 | Обидва limit switch активні, RESET у ERROR і поза ним | Functional, recovery | System | P1 | ERROR один раз, relay OFF, без циклу повідомлень; RESET у ERROR → CLOSED; RESET поза ERROR нічого не змінює (R10–R12) |
| TM-05 | QR-02 · T1-04, 05, 08, 12 | Стан LED після STOP, diagnostic для некоректних команд, одна команда на натискання | Functional, reliability | Component | P2 | OPEN LED OFF у STOPPED; diagnostic друкується; одне натискання — один COMMAND (R13, R14, R16) |
| TM-06 | QR-03 · T3-05 | Межі довжини рядка: 40, 41, 200, 1000 символів | Boundary / negative | Interface / protocol | P1 | 40 — команда; 41+ → «ERROR: command too long»; без SYSTEM FAULT і reboot (REQ-11, 12, 14, 16) |
| TM-07 | QR-03 · T3-01…04 | Валідація значень і синтаксису CLI | Boundary / negative | Component | P2 | Невалідний ввід → «ERROR», значення збережене (REQ-03, 05, 06, 08) |
| TM-08 | QR-04 · T5-01 | Persistent counter після powerloss під час save | Persistence, recovery | Recovery / fault injection | P1 | Старе значення або old+1; пошкодження залоговано; 5 з 5 запусків (R6) |
| TM-09 | QR-05 · T7-03 | Overflow offline buffer: SEND ×8, ×9, ×12, STRESS 100 | Network stress, boundary | Network | P1 | buffer ≤ 8; для 12 повідомлень buffer=8, dropped=4 (R4) |
| TM-10 | QR-05 · T7-02, 05 | Flush після NET UP зі слідкуванням за ID | Functional, network stress | Network | P1 | Кожен ID один раз, від найстарішого; duplicates=0 (R5, R6, R8) |
| TM-11 | QR-06 · T7-04 | Memory stability: STRESS 100 ×10, 20 циклів reconnect | Memory stability | System | P1 | Втрата heap менша за 5% (R7) |
| TM-12 | QR-07 · T2-01 | Sweep імпульсу NOISE 0.5, 1, 2, 10, 20, 29, 30 мс | Boundary, automation | Component | P2 | Нижче порогу → 0 events; реальне натискання → 1 event і 1 action (AC4, AC5) |
| TM-13 | QR-07 · T2-01 | Шум під час critical action і пауза 15 мс між натисканнями | Reliability, automation | Component | P2 | Шум не додає event; Actions = кількість реальних натискань |
| TM-14 | QR-08 · T4-01, 02 | I2C після NACK: FAULT on → off у відомий момент, capture ≥ 30 с | Protocol, recovery | Interface / protocol | P2 | Retry або повідомлення про втрату; опитування 0x68 відновлюється; без тиші 33 с |
| TM-15 | QR-09 · T6-01, 02, 03 | JSON-протокол: валідність, SET PWM 0 / 1 / 99 / 100 / 101, RESET | Protocol, boundary | Interface / protocol | P2 | json.loads для кожної відповіді; PWM 0–100 → OK, 101 → INVALID_VALUE; RESET → led=false, pwm=0 |
| TM-16 | QR-09 · T6-04 | Час відповіді PING і STATUS | Protocol, reliability | Interface / protocol | P3 | Порівнянний час; STATUS після PING не затримується (ліміт погодити з власником вимог) |
| TM-17 | QR-10 · T5-02, 05 | sleep N = 3, 5, 10, 20, 60 с за часом firmware | Recovery | Recovery / fault injection | P2 | Wake-up у межах N ±15% за таймером; 60 с не завершується INT_WDT |
| TM-18 | QR-10 · T5-03 | Watchdog: hang, вимірювання часу до reset | Recovery | Recovery / fault injection | P2 | Reset за 5 с ±15%, reset reason INT_WDT, нормальний старт |
| TM-19 | QR-10 · T5-04 | Некоректні аргументи sleep | Boundary / negative | Component | P3 | Повідомлення про помилку, значення не збережене |
| TM-20 | QR-11 · T7-01 | Backoff під час 20-секундного outage | Network stress | Network | P3 | Не більше 12 retry за 20 с, зростаючий backoff (R2) |
| TM-21 | QR-05, 11 · T7-06, 07 | Некоректні аргументи STRESS, повторні fault-команди | Boundary / negative | Component | P3 | «[CLI] ERROR»; повторний NET DOWN / UP нічого не змінює |
| TM-22 | QR-12 | Закрити open questions і повторити TM-01, 08, 14 на real hardware | Functional, protocol, recovery | System (real hardware) | P3 | Рішення задокументовані; три ключові тести пройдено на стенді |

Покриття: 22 тести (9 × P1, 8 × P2, 5 × P3); кожен із 36 defects має хоча б один рядок.

## 8. Test Levels

| Рівень (вебінар) | Що перевіряє | Наше покриття |
|---|---|---|
| Component / interface checks | Окремі компоненти та інтерфейси: команди, формати даних | TM-05, 07, 12, 13, 19, 21; Tasks 2, 3, 6 |
| Integration testing | Взаємодія модулів і сервісів, обмін даними між компонентами | **Прогалина:** збірки окремі; частково — firmware ↔ сенсор (I2C, Task 4) і firmware ↔ broker (Task 7) |
| System black-box testing | Вся система без знання реалізації: функціональні сценарії, вимоги, бізнес-логіка | TM-01…04, 11; Tasks 1, 7 |
| Fault injection | Навмисні помилки: збої живлення, timeouts, обриви зв'язку | TM-08, 14, 17, 18; Tasks 4, 5 (powerloss, hang, FAULT, NET DOWN) |
| Non-functional / reliability | Стрес, навантаження, витривалість, відновлення | TM-09, 10, 11, 20; Task 7 (STRESS, 391 retry, heap) |
| Automation / regression | Автотести, regression-набір | pytest (Tasks 5–7), Wokwi CLI (Tasks 2, 3); Tasks 1 і 4 — manual |

## 9. Test Types

| Type | Tasks | Приклад результату |
|---|---|---|
| Functional | 1, 3, 6, 7 | Стан OPEN ніколи не досягається (T1-02) |
| Boundary / negative | 2, 3, 5, 6, 7 | speed 256 → 255 (T3-01); SET PWM 100 відхилено (T6-01) |
| Protocol | 3, 4, 6 | GET TEMP без закривної дужки (T6-03) |
| Reliability | 1, 2, 3 | Нульовий debounce: 3–6 команд на натискання (T1-12) |
| Recovery | 4, 5 | Watchdog reset через 14.59 с замість 5 с (T5-03) |
| Persistence | 5 | Counter 8 → 108 після powerloss (T5-01) |
| Network stress | 7 | 391 retry за 20 с (T7-01) |
| Memory stability | 7 | Heap −80 004 B (−23.2%) (T7-04) |
| Automation | 2, 3, 5, 6, 7 | pytest і Wokwi CLI suites із verdicts |

## 10. Test Environment

| Environment | Призначення | Інструменти | Де в пакеті |
|---|---|---|---|
| Wokwi simulation | Симуляція MCU і периферії, швидка перевірка логіки | Wokwi 3.7.0 (Task 1); Wokwi CLI v0.27.1 + scenario YAML (Tasks 2–7) | `tests/wokwi_scenarios/` |
| Serial / CLI | Взаємодія через послідовний порт (USB / UART) | Serial monitor, PlatformIO device monitor, команди help / status / set | `logs/` |
| Logic Analyzer + PulseView | Захоплення й аналіз цифрових сигналів (I2C, SPI, UART) | Capture sigrok `.sr`, Protocol Analysis Sheet (Task 4) | `test-results/i2c_failure.sr`, `test-results/task4_i2c/` |
| Python + Pytest | Автоматизація, генерація даних, перевірка очікуваних результатів | Python 3.9.12, pytest 8.4.2, pyserial (RFC2217) | `tests/pytest/` |
| MQTT / network environment | Publish / доставка повідомлень, мережеві сценарії | Симульований MQTT broker, команди NET DOWN / NET UP | `logs/task7_network_memory/` |
| Real hardware | Фізична валідація: електричні характеристики, надійність | Не використовувалось; обов'язковий gate перед release | — |

## 11. Entry Criteria (вхідні критерії)

Результат: команда впевнена, що все готово для ефективного та якісного виконання тестів.

| Критерій | Що перевіряємо | Статус у Tasks 1–7 |
|---|---|---|
| Firmware build доступний | Стабільна версія, успішна збірка, версія промаркована, базовий функціонал працює, документ із номером версії | Частково: збірки названі (v2.0, homework_buggy, BUGGY), ELF SHA256 зафіксовано лише в Task 5 |
| Requirements / expected behavior визначені | Актуальні вимоги, acceptance criteria, опис очікуваної поведінки (edge cases), погодження з командою | Так для Tasks 1 (R1–R16), 2 (AC1–AC5), 3 (REQ-01…16), 6 (Req. 1–9), 7 (R1–R8); для Task 4 вимог немає (неявні очікування) |
| Test environment готовий | Плати / стенди, інструменти (Wokwi, LA, MQTT), потрібні сервіси й дані, доступи | Так: версії інструментів зафіксовано; real hardware відсутній |
| Known limitations задокументовані | Список відомих проблем, тимчасові обмеження, непідтримувані сценарії, план виправлень | Частково: open questions у Consolidated Bug Report; офіційного списку обмежень немає |
| Critical interfaces доступні для спостереження | UART / CLI, SPI / I2C / GPIO, мережа (Wi-Fi, MQTT), логи та debug-інформація | Так для UART / логів (Tasks 2, 3, 5, 6, 7) і I2C (Task 4, лише logic analyzer); SPI немає |

## 12. Exit Criteria (вихідні критерії)

| Критерій | Умова виходу | Поточний статус |
|---|---|---|
| Critical scenarios виконані | Усі критичні сценарії (запуск, основний потік, передача даних, recovery після помилки) протестовані й працюють | ✖ Виконані, але **не працюють як очікується**: 9 Blocker / Critical |
| Немає відкритих Blocker / Critical defects | Blocker = 0, Critical = 0 | ✖ Blocker 5 (Task 1), Critical 4 (Task 3: 1, Task 7: 3) |
| Regression пройдений | Покриття regression 100% після змін | ✖ Не виконувався: виправлень ще немає |
| Recovery scenarios підтверджені | Перезавантаження, втрата живлення, втрата зв'язку, збій прошивки, пошкодження даних | ✖ Powerloss (T5-01), watchdog (T5-03), NACK (T4-01) і мережа (T7-05) провалені |
| Evidence збережений | Звіти тестів, логи, скріншоти, вимірювання, відео доступні для перегляду | Частково: логи, traces, звіти — так; Wokwi-скріншоти та відео — ні |
| Known risks прийняті або задокументовані | Відомі ризики оцінені, прийняті командою або задокументовані | Частково: ризики задокументовані (розділ 16); не прийняті |

**Статус defects (як зафіксовано в Tasks):**

| Blocker | Critical | Major | High | Medium | Minor / Low / Trivial | Без severity |
|---|---|---|---|---|---|---|
| 5 | 4 | 13 | 4 | 3 | 6 | 1 (T1-07, «Intermittent») |

Додаткові кількісні умови: безпека — relay ніколи не активні разом у 20 реверсах поспіль; heap — втрата менша за 5% після 10 × STRESS 100; мережа — не більше 12 retry за 20 с, duplicates=0; recovery — watchdog за 5 с ±15%, wake-up за N ±15%.

## 13. Regression Strategy (Крок 3)

| Рівень regression | Склад | Коли запускаємо | Конкретно в проєкті |
|---|---|---|---|
| Дим-тест (smoke) | boot + basic CLI + sensor + MQTT | Після кожної збірки | Boot banner і STATUS у кожній збірці; Task 3: help / status; Task 6: PING, STATUS, GET TEMP; Task 7: STATS і один publish; Task 4: один нормальний I2C-цикл; Task 1: CLOSED + команди O / C |
| Критичний regression | control + data integrity + recovery | Після виправлення Blocker / Critical | TM-01…04 (керування), TM-08, 10 (цілісність даних), TM-06, 11, 17, 18 (recovery і стабільність) |
| Повний regression | functional + protocol + power + network + stress | Перед release | Усі 22 тести матриці: pytest Task 5 (≈7.8 хв), Task 6 (≈10.4 хв), Task 7 (≈4.4 + 8.7 хв), Wokwi CLI Tasks 2 і 3, ручні Tasks 1 і 4 |
| Автоматизація | Запускаємо там, де перевірки повторювані та детерміновані | Постійно | Tasks 2, 3, 5, 6, 7 автоматизовані; Tasks 1 і 4 — кандидати на автоматизацію |

Після кожного fix: провалений тест + сусідні з початковою кількістю повторів. Перед release: усі suites і один прогін на real hardware для Tasks 1, 4, 5.

## 14. Evidence Strategy

| Evidence (вебінар) | Що саме | Файли пакета | Статус |
|---|---|---|---|
| Screenshot / video | Знімки екрана або відео підтверджують результат | `screenshots/*.png` (рендери PDF-експортів terminal і графік heap) | Частково: Wokwi-вікна та відео немає |
| Serial log | Обмін даними та події | `logs/task2…task7/` | Є |
| PulseView trace | Трейс протоколу I2C | `test-results/i2c_failure.sr` | Є (один capture) |
| Wokwi project | Проєкт Wokwi для відтворення | `tests/wokwi_scenarios/task3_uart_cli/` (сценарії) | Частково: файлів diagram.json немає в архіві |
| Pytest report | Звіти автотестів | `test-results/task6_protocol/pytest_output.txt`, `test-results/task5_recovery/pytest_log_task5.pdf`, `test-results/task7_network_memory/` | Є |
| Memory stability log | Використання пам'яті, витоки | `logs/task7_network_memory/`, `logs/network_stress.csv`, `screenshots/task7_heap_trend.png` | Є |
| Bug report | Дефект зі steps, expected, actual, логами | Appendix A, `test-results/task1_gate/Bug_Report_Serhii_Shtelmakh.xlsx`, Consolidated Bug Report | Є |
| Test summary | Покриття, кількість, результати | `test-results/reports/test_summary.md` | Є |

### 14a. Evidence Package: схема `final-report/` і відповідність Evidence Index

```
final-report/
├── README.md                    опис звіту, зміст, як користуватись
├── master-test-plan.md          план тестування та критерії (цей файл)
├── test-results/                результати тестів (логи, тести, артефакти)
│   ├── i2c_failure.sr           трасування I2C збоїв (Task 4)
│   ├── task1_gate/ … task7_network_memory/
│   └── reports/                 Risk Matrix, Case Study, Evidence Index, Test Summary
├── logs/                        логи тестів та системи
│   ├── network_stress.csv       дані стрес-тестів мережі (Task 7)
│   └── task2_debounce/ … task7_network_memory/
├── tests/                       скрипти та тести
│   ├── pytest/                  Task 6, Task 7 (Python)
│   └── wokwi_scenarios/         Task 3 (YAML-сценарії)
└── screenshots/                 скріншоти інтерфейсів, графіків, помилок
```

| Evidence ID | R (Evidence Index) | Webinar R | Де в пакеті |
|---|---|---|---|
| E01 | R01 debounce | — | `logs/task2_debounce/`, `test-results/task2_debounce/` |
| E02 | R02 pytest / CLI | R1 | `test-results/task6_protocol/pytest_output.txt`, `logs/task6_protocol/` |
| E03 | R03 I2C trace | R2 | `test-results/i2c_failure.sr`, `test-results/task4_i2c/` |
| E04 | R04 watchdog | R3 | `logs/task5_recovery/`, `test-results/task5_recovery/` |
| E05 | R05 persistence | R4 | `logs/task5_recovery/serial_20261014_152215.log` (рядки 173–187) |
| E06 | R06 reconnect | R5 | `logs/task7_network_memory/`, `logs/network_stress.csv` |
| E07 | R07 message IDs | R5 | `logs/task7_network_memory/device-monitor-261024-174403.log` |
| E08 | R08 heap | R6 | `logs/network_stress.csv`, `screenshots/task7_heap_trend.png` |
| E09–E11 | Tasks 1, 3, 6 | R1, R3 | `test-results/task1_gate/`, `logs/task3_uart_cli/`, `logs/task6_protocol/` |

Правило: evidence має дозволяти іншій людині перевірити висновок QA — для кожного пункту в `test-results/reports/EVIDENCE_INDEX_UA.md` є conclusion і спосіб перевірки.

### 14b. Від доказів до рішення

Вимога / ризик → тестування (приоритетні ризики) → докази (логи, скріншоти, звіти, вимірювання) → знахідки (дефекти, відхилення, спостереження) → рішення: **Go** (критерії виконані), **No-Go** (критерії не виконані, реліз неможливий без виправлень) або **Known Risk** (реліз можливий з обмеженнями та планом моніторингу). Для цього проєкту результат — **No-Go**.

## 15. Defect Management

- **Поля:** ID, title, requirement, severity, reproducibility (n/N), environment, steps, expected, actual, evidence, status.
- **Severity:** єдина шкала надалі — Blocker / Critical (safety, crash, втрата даних), High, Medium, Low, Trivial. Reproducibility — окреме поле й не є severity (T1-07).
- **Priority:** визначається ризиком (розділ 7), а не лише severity.
- **Retest:** defect закривається, коли тест проходить у всіх повторах і regression-набір зелений.
- Open questions (прогалини у вимогах) ведуться окремо й не рахуються як defects.

| Task | Defects | Severity як зафіксовано | Verdict |
|---|---|---|---|
| 1 | 12 | 5 Blocker, 3 Major, 3 Minor, 1 «Intermittent» | FAIL |
| 2 | 1 | 1 Major | FAIL |
| 3 | 5 | 1 Critical, 4 Major | Not ready for release |
| 4 | 2 | 2 High | FAIL |
| 5 | 5 | 3 Major (High), 2 Medium | NO-GO |
| 6 | 4 | 2 High, 1 Medium, 1 Low / Medium | Неприйнятно, поки BUG-1…3 не виправлено |
| 7 | 7 | 3 Critical, 2 Major, 1 Minor, 1 Trivial | FAIL |
| **Разом** | **36** | | |

## 16. Residual Risks / Known Risks

| Відомий ризик | Чому залишається | Статус | План |
|---|---|---|---|
| Результати лише з симуляторів | Relay timing, contact bounce, електрика I2C, brown-out не доведені | Задокументовано, не прийнято | Real hardware gate (TM-22) |
| Task 4 — один capture | Невідомо, чи відновлюється пристрій після вимкнення FAULT | Задокументовано | Повторити з FAULT off у відомий момент |
| Таймінги Task 5 з simulator clock | T5-02, T5-03 потребують часу firmware | Задокументовано | Перемірити за firmware time |
| Пороги без вимог | Debounce, PWM-одиниці, I2C recovery, latency PING | Open questions | Погодити з власником вимог |
| Не протестовано | Стан relay після watchdog reset (тест завершився ERROR), збій DHT22, long outage, 300 с watchdog, втрата saved config після crash | Задокументовано | Додати в наступний цикл |
| SPI, реальний Wi-Fi, security | Поза збірками | Out of Scope | — |
| Приховані defects | T1-03 ховає R15, поки OPEN недосяжний | Задокументовано | Retest після fix |
| Evidence-прогалини | Немає Wokwi-скріншотів, відео та diagram.json | Задокументовано | Доповнити пакет |

## 17. Release Recommendation

Документи рішення: [Release_Decision_UA.md](test-results/reports/Release_Decision_UA.md) (рішення, Exit Criteria, умови Go, план виправлень) і [QA_Conclusion_UA.md](test-results/reports/QA_Conclusion_UA.md) (висновок QA).

**NO-GO.**

- 36 defects відкриті, усі сім збірок не пройшли або not ready.
- Залишається 9 Blocker / Critical defects: relay одночасно (T1-06, T1-09), OPEN недосяжний і не відновлюється (T1-02, T1-03, T1-11), crash від довгого UART-рядка (T3-05), overflow buffer, витік heap і втрата повідомлень (T7-03, T7-04, T7-05).
- Data integrity (T5-01) і коректність протоколу (T6-02, T6-03) також порушені, тож **GO WITH RISKS (Known Risk)** не обґрунтований.
- Умови для переоцінки: виправити й повторно перевірити Blocker / Critical і High defects, виконати Exit Criteria (розділ 12), повторити ключові safety- і recovery-тести на real hardware.
- **Хто приймає рішення:** Product owner та test manager; ця рекомендація — висновок QA-інженера.

## Appendix A. Consolidated Bug Report — Embedded QA (Tasks 1–7)

Severity збережено як у кожному Task. Повні steps, expected / actual і фрагменти log — у [Consolidated Bug Report](https://claude.ai/artifact/6KQzyjYGmvvRQ8JC5DY618) і в `test-results/reports/EVIDENCE_INDEX_UA.md`.

| ID | Defect | Severity | Reproducibility |
|---|---|---|---|
| T1-01 | Movement timeout не переводить OPENING → ERROR | Major | 5/5 |
| T1-02 | OPEN limit не переводить ворота в OPEN | Blocker | 5/5 |
| T1-03 | Стан OPEN недосяжний, R15 неможливо перевірити | Blocker | 5/5 |
| T1-04 | OPEN LED лишається ON після STOP з OPENING | Minor | 5/5 |
| T1-05 | OPEN LED лишається ON після STOP з CLOSING | Minor | 5/5 |
| T1-06 | Протилежна команда реверсує напрямок без safe stop | Blocker | 5/5 |
| T1-07 | Обидва limit switch активні: warning loop замість ERROR | «Intermittent» (потрібна переоцінка) | 5/5 |
| T1-08 | Некоректна команда в CLOSED мовчки ігнорується | Minor | 5/5 |
| T1-09 | Обидва relay коротко активні під час реверсу | Blocker | 4/5 |
| T1-10 | RESET поза ERROR змінює стан | Major | 5/5 |
| T1-11 | RESET не очищає цикл limit switch | Blocker | 5/5 |
| T1-12 | Нульовий debounce: одне натискання — кілька команд | Major | 5/5 |
| T2-01 | NOISE-імпульси від 2 мс приймаються як натискання | Major / High | 5/5 |
| T3-01 | set speed 256 прийнято й встановлено в 255 | Major / Medium | 5/5 |
| T3-02 | set timeout 0 прийнято | Major / Medium | 5/5 |
| T3-03 | status не case-insensitive | Major / Medium | 5/5 |
| T3-04 | Рядок лише зі спецсимволів прийнято як валідну команду | Major / Medium | 5/5 |
| T3-05 | Ввід довший за 40 символів валить і перезавантажує пристрій | Critical / High | 5/5 |
| T4-01 | Після першого NACK пристрій припиняє всю I2C-активність | High | 1/1 capture |
| T4-02 | Після NACK не видно recovery чи reboot | High (proposed) | 1/1 capture |
| T5-01 | Перерване збереження лишає counter = old+100, не виявлено | Major (High) | 5/5 |
| T5-02 | Час wake-up ігнорує задану тривалість sleep | Major (High) | 5/5 |
| T5-03 | Watchdog reset через ≈14.6 с замість 5 с | Major (High) | 1 вимірювання |
| T5-04 | sleep приймає некоректні аргументи й мовчки підміняє значення | Medium | 18/18 |
| T5-05 | 60-секундний sleep завершується watchdog reset | Medium | 6/6 |
| T6-01 | SET PWM 100 повертає INVALID_VALUE | Medium | 5/5 |
| T6-02 | RESET відповідає OK, але не скидає LED і PWM | High | 5/5 |
| T6-03 | GET TEMP повертає invalid JSON | High | 100% |
| T6-04 | PING блокує обробку команд ≈1.3 с | Low / Medium | 100% |
| T7-01 | Reconnect storm, ≈19 retry на секунду | Major / Medium | 5/5 |
| T7-02 | Кожне буферизоване повідомлення публікується двічі після NET UP | Major / Medium | 6/6 |
| T7-03 | Buffer росте понад capacity 8, нічого не відкидається | Critical / High | 4/4 |
| T7-04 | Витік heap, 80 B на повідомлення | Critical / High | 5/5 |
| T7-05 | Flush після overflow губить найстаріші повідомлення й повторює інші | Critical / High | 4/4 |
| T7-06 | Некоректні аргументи STRESS мовчки виконуються як count=1 | Minor / Low | 2 запуски |
| T7-07 | Fault-команди не є idempotent | Trivial / Low | 2 запуски |
