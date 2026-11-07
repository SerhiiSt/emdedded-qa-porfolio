# QA Conclusion — Embedded QA (Tasks 1–7)

Висновок QA за результатами тестування семи firmware-збірок Smart IoT Safety Controller. Підготував Serhii, QA Embedded Engineer, 2026-11-01.

Пов'язані документи: [master-test-plan.md](master-test-plan.md) · [Release_Decision_UA.md](Release_Decision_UA.md) · [Risk_Matrix_UA.md](Risk_Matrix_UA.md) · [Test_Matrix_UA.md](Test_Matrix_UA.md) · [EVIDENCE_INDEX_UA.md](EVIDENCE_INDEX_UA.md) · [case_study_UA.md](case_study_UA.md)

## 1. Загальний висновок

Сім збірок було протестовано risk-based методом у симуляторах (Wokwi, Wokwi CLI, pytest, logic analyzer). Знайдено **36 defects**, з них 9 Blocker / Critical. Жодна збірка не відповідає Exit Criteria, а всі шість критичних ризиків R1–R6 підтверджені дефектами. **Рекомендація: NO-GO** (див. [Release_Decision_UA.md](Release_Decision_UA.md)).

Найсерйозніше: збірки добре «працюють у happy path», але ламаються на межах, під fault і при повторному recovery — саме там, де продукт має поводитись передбачувано. Це відповідає меті продукту: стабільна робота при hardware noise, protocol faults, hangs, power / network faults і repeated recovery.

## 2. Що тестували і що довели

| Task | Збірка | Що тестували | Висновок QA | Defects |
|---|---|---|---|---|
| 1 | Smart Gate Controller | State machine, relay interlock, limit switches, RESET, debounce кнопок | Функція безпеки не гарантована: relay можуть бути активні разом, ворота не досягають OPEN і не відновлюються | 12 |
| 2 | Button Debounce | Sweep імпульсів 0.5–30 мс, шум під час action | Ефективний поріг debounce 1–2 мс; шум запускає зайві дії | 1 |
| 3 | UART CLI | Boundary і negative-ввід, довжина рядка, валідація значень | Один довгий рядок перезавантажує пристрій; валідація неповна | 5 |
| 4 | I2C sensor polling | NACK і поведінка шини | Після одного NACK пристрій мовчить 33.09 с без повідомлення | 2 |
| 5 | Recovery / Fault Injection | Powerloss, hang, sleep, некоректні аргументи | Дані пошкоджуються без індикації; таймінги recovery не відповідають вимогам | 5 |
| 6 | JSON serial protocol | Валідність JSON, межі PWM, RESET, час відповіді | Контракт протоколу порушено: RESET не скидає, GET TEMP — invalid JSON | 4 |
| 7 | IoT network / memory | Reconnect, buffer, flush, STRESS, heap | Втрата й дублювання даних, витік пам'яті, reconnect storm | 7 |

## 3. Стан критичних ризиків R1–R6

| R | Ризик | Висновок | Score | Evidence |
|---|---|---|---|---|
| R1 | Неправильна команда керування | **Підтверджено**: невалідні значення приймаються, RESET не діє, relay перекриваються | 9 / 6 | [Test_Matrix_UA.md](Test_Matrix_UA.md): TM-01…07, 12, 13, 15 |
| R2 | Датчик недоступний | **Підтверджено** для I2C (NACK); DHT22 не тестувався | 6 | [i2c_failure.sr](pulseview/task4_i2c/i2c_failure.sr) |
| R3 | Зависання прошивки | **Підтверджено**: crash від довгого рядка; watchdog через 14.59 с замість 5 с | 9 / 6 | [TC-27.log](wokwi/task3_uart_cli/logs/TC-27.log), [serial log Task 5](pytest/task5_recovery/logs/serial_20261014_152215.log) |
| R4 | Втрата живлення під час збереження | **Підтверджено**: counter 8 → 108, пошкодження не виявлено | 9 | [serial log Task 5](pytest/task5_recovery/logs/serial_20261014_152215.log) (рядки 173–187) |
| R5 | Мережа недоступна | **Підтверджено**: overflow без drop, дублікати й втрата ID, reconnect storm | 9 / 4 | [device-monitor log](network-stress/task7_network_memory/logs/device-monitor-261024-174403.log) |
| R6 | Деградація пам'яті | **Підтверджено**: −80 004 B (−23.2%) за 10 × STRESS 100 | 9 | [heap trend](network-stress/task7_network_memory/screenshots/task7_heap_trend.png) |

## 4. Що працює правильно (позитивні знахідки)

QA-висновок має бути збалансованим: частину перевірок firmware проходить, і це теж evidence.

- **Task 1:** movement timeout у CLOSING працює (R9): виводиться «ERROR: movement timeout» і стан переходить у ERROR.
- **Task 2:** імпульси 0.5 і 1 мс ігноруються правильно (`Logical events: 0`).
- **Task 3:** 40 символів обробляються як команда; speed −1, 999, 100000 та timeout 61, −5 відхиляються; HELP повертає «ERROR: unknown command».
- **Task 4:** після NACK шина відпускається коректно (SDA і SCL у high), до NACK тривали нормальні цикли опитування 0x68 (близько 608).
- **Task 5:** boot і reset reason відображаються правильно; після watchdog пристрій відновлюється без boot loop (`test_no_boot_loop_after_wdt` — PASSED); `test_powerloss_recovers` — PASSED.
- **Task 6:** PWM 99 → OK і 101 → INVALID_VALUE (тобто помилка лише на межі 100); control-тест «дві команди STATUS в одному записі відповідають швидко» проходить.
- **Task 7:** рівно 8 повідомлень у buffer обробляються правильно; після NET UP вузол відновлює з'єднання приблизно за 3 мс.

## 5. Наскрізні закономірності (root-cause patterns)

1. **Межі й валідація.** Defects концентруються на boundary: 256, 0, 41 символ, PWM 100, STRESS −5. Кінцеві значення пропущено в реалізації або перевірці (T3-01, T3-02, T3-05, T6-01, T7-06).
2. **RESET і recovery.** Команди відновлення відповідають OK, але нічого не роблять або роблять не те (T1-10, T1-11, T6-02): safe state не гарантований.
3. **Тихі збої.** Пристрій не повідомляє про проблему: корупція counter (T5-01), тиша I2C (T4-01), підміна аргументів sleep (T5-04), недосяжний DROP_OLDEST (T7-03).
4. **Асиметрія реалізації.** Timeout працює в CLOSING, але не в OPENING (T1-01); `HELP` відхиляється, а `Status` виконується (T3-03).
5. **Таймінги.** Wake-up, watchdog і backoff не відповідають очікуванням (T5-02, T5-03, T7-01).
6. **Прогалини у вимогах.** Для I2C recovery, latency PING, одиниць PWM і порогу debounce вимог немає — це вплинуло на Expected Result і винесене в open questions.

## 6. Метрики

| Показник | Значення |
|---|---|
| Збірок протестовано | 7 |
| Тестів у Test Matrix | 22 (9 × P1, 8 × P2, 5 × P3); 21 FAIL, 1 не виконано |
| Автоматизованих тестів (Tasks 2, 5, 6, 7) | 232: 139 passed, 77 failed, 7 skipped, 4 xfailed, 2 errors, 3 REVIEW / INVALID — pass rate 59.9% |
| Defects | 36: 5 Blocker, 4 Critical, 13 Major, 4 High, 3 Medium, 6 Minor / Low / Trivial, 1 без severity |
| Ключові вимірювання | Heap −80 004 B (−23.2%); 391 retry за 20 с; watchdog 14.59 с; тиша I2C 33.09 с; counter +100 |

Кількість failed у pytest включає тести, написані для виявлення підозрілого bug, і не дорівнює кількості defects.

## 7. Рівень впевненості та обмеження

| Висновок | Впевненість | Чому |
|---|---|---|
| Дефекти T1, T3, T5-01, T6, T7 | Висока | Відтворені повторно (4/5 … 26/26), підтверджені log і/або ручною перевіркою |
| T2-01 | Висока для поведінки; Середня щодо порогу | Поріг debounce ≈ 30 мс — припущення |
| T4-01, T4-02 | Середня | Один capture, немає log firmware, невідомо, коли вимкнено FAULT |
| T5-02, T5-03 | Середня | Час із simulator clock, потрібне підтвердження за часом firmware |
| Повна відсутність recovery після NACK, brown-out, relay timing | Невідомо | Потрібен real hardware |

Обмеження: тільки симулятори; SPI і реальний Wi-Fi не тестувались; рівня Integration testing між збірками немає; не перевірено стан relay після watchdog reset (тест завершився ERROR), збій DHT22, long outage, 300 с watchdog, втрату saved config після crash у Task 3; немає Wokwi-скріншотів і відео.

## 8. Рекомендації

**Для розробки (за пріоритетом):** interlock і safe stop для relay → досягнення OPEN і відновлення → ліміт довжини рядка та валідація CLI → цілісність persistent counter (CRC / атомарний запис) → логіка buffer і flush, витік heap → контракт JSON-протоколу → recovery і таймінги → debounce та діагностичні повідомлення. Повний план — у [Release_Decision_UA.md](Release_Decision_UA.md), розділ 9.

**Для процесу тестування:**
- Одна шкала severity; reproducibility — окреме поле (T1-07).
- Закрити open questions із власниками вимог до наступного циклу.
- Автоматизувати Tasks 1 і 4, додати relay-interlock перевірку до smoke-набору.
- Додати Wokwi-скріншоти, відео та файли проєкту до evidence package.
- Перемірити Task 5 за часом firmware; повторити TM-01, TM-08, TM-14 на real hardware.

## 9. Висновок для захисту (Problem → Result)

**Проблема:** чи безпечні, відновлювані й стабільні семеро firmware-збірок?
**Аналіз ризиків:** 12 Quality Risks, шість з score 9, шість критичних R1–R6.
**Test design:** 22 тести Test Matrix: boundary / negative, fault injection, recovery, network stress, memory stability, automation.
**Виконання й evidence:** логи, I2C trace, pytest-звіти, метрики heap, bug reports ([Evidence Index](EVIDENCE_INDEX_UA.md)).
**Знахідки:** 36 defects, 9 Blocker / Critical.
**Висновок:** **NO-GO**; Go можливий після виправлень, retest і прогону на real hardware.
