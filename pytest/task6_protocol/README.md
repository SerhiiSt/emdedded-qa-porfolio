# Task 6 — JSON serial protocol (pytest)

## Project goal

Перевірити контракт JSON-протоколу по UART: коректність відповідей, межі параметрів, команду RESET, час відповіді (Req. 1–9).

## System under test

ESP32, LED, PWM-вихід, датчик температури; збірка BUGGY. Команди PING, STATUS, GET TEMP, SET LED, SET PWM (0–100), RESET; одна JSON-відповідь на команду.

## Test strategy

Risk-based: QR-09 (score 6, P2). Протокол і boundary / negative: валідність JSON, SET PWM 0 / 1 / 99 / 100 / 101, RESET після SET LED і SET PWM, вимірювання часу PING і STATUS; control-тести для відокремлення defect від harness. Тести: TM-15, TM-16.

## Environment & tools

Python 3.9.12, pytest 8.4.2, pyserial через RFC2217, Wokwi CLI v0.27.1; ручна перевірка `manual_check.py`.

## Key scenarios

1. `GET TEMP` → `{"status":"OK","temperature":24.5` без закривної дужки (json.loads падає).
2. `SET PWM 100` → INVALID_VALUE (99 — OK, 101 — коректна помилка).
3. `RESET` → OK, але STATUS: `led=true, pwm=127`.
4. `PING` відповідає за 1.31–1.40 с; STATUS одразу після PING — 1.46 с.

## Bugs / findings

Severity як зафіксовано в Task: 2 High, 1 Medium, 1 Low / Medium. Усього defects: 4.

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T6-01 | SET PWM 100 повертає INVALID_VALUE | Medium | 5/5 | {"status":"OK","pwm":100} (Req. 5) | {"status":"ERROR","code":"INVALID_VALUE"} |
| T6-02 | RESET відповідає OK, але не скидає LED і PWM | High | 5/5 | led=false, pwm=0 (Req. 7) | led=true, pwm=127 (або 255) |
| T6-03 | GET TEMP повертає invalid JSON | High | 100% | Валідний JSON (Req. 3) | {"status":"OK","temperature":24.5 без закривної дужки |
| T6-04 | PING блокує обробку команд приблизно 1.3 с | Low / Medium | 100% | PING відповідає швидко, як STATUS | 1.31–1.40 с; медіана у 5.7 раза більша за STATUS |

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [pytest_output.txt](pytest_output.txt) — 96 тестів: 17 failed, 72 passed, 2 skipped, 4 xfailed, 1 error (623.14 с)
- [logs/manual_check_1.log](logs/manual_check_1.log) — ручна перевірка, [logs/pytest_cases/](logs/pytest_cases/) — окремі логи тестів
- [tests/](tests/) — `conftest.py`, `device.py`, `manual_check.py`
- [Python_Pytest_Test_Sheet_Webinar_6_filled.docx](Python_Pytest_Test_Sheet_Webinar_6_filled.docx), [logs_terminal_task6.pdf](logs_terminal_task6.pdf), скріншот [task6_terminal_log.png](screenshots/task6_terminal_log.png)

Прогалини: файли test_*.py відсутні в архіві (збережені лише helpers); QUESTION-1 (одиниці PWM) і QUESTION-2 (LED / PWM) — open questions, не defects.

## What I learned / decisions made

- Defect підтверджено двома шляхами (pytest і ручний лог), тому його не можна списати на harness.
- Один pytest ERROR був помилкою виконання («No response for command: RESET»), а не firmware bug.
- Рішення: залишати control-тести (дві команди STATUS в одному записі), які проходять, щоб довести справність test setup.
