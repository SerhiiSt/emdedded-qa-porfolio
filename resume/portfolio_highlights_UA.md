# Portfolio Highlights — QA Embedded Engineer

Матеріал для резюме та співбесіди на основі семи проєктів портфоліо. Усі твердження підкріплені evidence з репозиторію.

## Навички, підтверджені портфоліо

| Навичка | Підтвердження | Де в репозиторії |
|---|---|---|
| Embedded QA strategy і Master Test Plan | 12 Quality Risks, Test Matrix із 22 тестів, Entry / Exit Criteria, рішення NO-GO | [master-test-plan.md](../master-test-plan.md), [Test_Matrix_UA.md](../Test_Matrix_UA.md), [Release_Decision_UA.md](../Release_Decision_UA.md) |
| Risk-based testing | Матриця Probability × Impact, 6 ризиків зі score 9 | [Risk_Matrix_UA.md](../Risk_Matrix_UA.md) |
| Black-box test design для embedded | Функціональні та boundary / negative тести воріт, debounce, CLI, протоколу | [wokwi/](../wokwi/) |
| UART / CLI boundary і stress tests | Crash на 41 символі (26/26), 36 сценаріїв | [wokwi/task3_uart_cli/](../wokwi/task3_uart_cli/) |
| I2C / logic analyzer (PulseView, sigrok) | Аналіз NACK і 33.09 с тиші на шині | [pulseview/task4_i2c/](../pulseview/task4_i2c/) |
| Fault injection, watchdog, powerloss, recovery | Counter +100 після powerloss, watchdog 14.59 с замість 5 с | [pytest/task5_recovery/](../pytest/task5_recovery/) |
| Python / pytest автоматизація | 232 автоматизовані тести в Tasks 2, 5, 6, 7 | [pytest/](../pytest/), [test_summary.md](../test_summary.md) |
| IoT network stress та memory stability | 391 retry за 20 с, витік heap −23.2%, втрата й дублювання повідомлень | [network-stress/](../network-stress/) |
| Evidence package і bug reporting | 36 defects з Expected / Actual, Evidence Index з командами перевірки | [bug-reports/BUG_REGISTER_UA.md](../bug-reports/BUG_REGISTER_UA.md), [EVIDENCE_INDEX_UA.md](../EVIDENCE_INDEX_UA.md) |

## Формулювання для резюме (за фактами портфоліо)

- Спроектував Master Test Plan і risk-based Test Matrix (22 тести, 12 Quality Risks) для семи embedded / IoT збірок на ESP32 і Arduino Uno.
- Виявив і задокументував 36 defects (9 Blocker / Critical), зокрема одночасне вмикання двох relay, crash від довгого UART-рядка, пошкодження persistent counter і витік heap (−23.2%).
- Проаналізував I2C-трасу в PulseView: NACK і 33 с мовчання шини після fault injection.
- Автоматизував перевірки на Python / pytest (pyserial, Wokwi CLI), зібрав evidence package з логами, traces, метриками та CSV-даними стрес-тесту.
- Сформував рекомендацію NO-GO з умовами повторної оцінки й планом виправлень.

## Питання співбесіди: відповіді з матеріалів проєкту

| Питання | Відповідь |
|---|---|
| Як би ви протестували кнопку? | Debounce, довге натискання, шум, edge cases, негативні тести: у Task 2 — sweep імпульсів 0.5–30 мс і шум під час critical action; виявлено поріг 1–2 мс замість ≈30 мс. |
| Що робити, якщо I2C sensor не відповідає? | Timeouts, retries, fallback, перевірка адреси, живлення, логування. У Task 4 після NACK пристрій мовчав 33 с без повідомлення — саме це я позначив defect-ом. |
| Як перевірити Watchdog? | Тести зависань, не годувати WDT, перевірка reset і reason: у Task 5 `hang` → reset через 14.59 с замість 5 с, reset reason INT_WDT. |
| Що станеться при втраті мережі? | Reconnect strategy, offline queue, збереження даних: у Task 7 backoff 50 мс (391 retry), buffer не обмежується, flush губить і дублює ID. |
| Що автоматизувати першим? | Smoke, критичні потоки, регресію, тести стабільності й відновлення: P1-набір TM-01, 02, 03, 04, 06, 08, 09, 10, 11 і STRESS 100 × 10. |
| Пристрій працює у Wokwi. Навіщо real hardware? | Симуляція підтверджує логіку, але не timing, noise, power behavior і реальні умови інтерфейсів: powerloss був командою, час — з simulator clock. |
| Автотест FAILED. Це firmware bug? | Ні, спочатку: test logic → environment → communication → requirement → firmware. У проєкті TC-15 (Task 7) — помилка тесту, pytest ERROR у Tasks 5 і 6 — не assertion firmware, а T6-03 підтверджено ще й вручну. |
| Як тестувати без повної документації? | Виділити observable inputs / outputs, зібрати known constraints, зафіксувати assumptions, будувати risk-based exploratory сценарії і не видавати припущення за requirements (Task 4 без вимог). |

Структура відповіді: проблема → підхід → приклад → результат; підкріплювати даними з evidence.
