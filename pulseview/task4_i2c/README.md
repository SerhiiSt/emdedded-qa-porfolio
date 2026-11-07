# Task 4 — I2C sensor polling (PulseView)

## Project goal

Проаналізувати I2C-обмін між ESP32 і датчиком MPU-6050 та поведінку пристрою після помилки (NACK).

## System under test

ESP32 + MPU-6050 по I2C: ініціалізація запису в регістр 0x6B, опитування адреси 0x68 приблизно кожні 1.001 с, перемикач FAULT. Вимог до I2C recovery немає (неявне очікування).

## Test strategy

Risk-based: QR-08 (score 6, P2). Fault Injection: увімкнути FAULT, зняти capture ≥ 30 с, проаналізувати транзакції, ACK / NACK, паузи. Тест: TM-14.

## Environment & tools

Logic analyzer capture у форматі sigrok (.sr), аналіз у PulseView, Protocol Analysis Sheet (xlsx).

## Key scenarios

1. Нормальні цикли: START → 0x68 W → 0x41 → Sr → 0x68 R → дані (близько 608 циклів).
2. FAULT on: START на 0x69 W (0xD2) → NACK на 9-му такті (89.4 µs після START) → STOP через 14.9 µs.
3. Після цього шина idle: 33.09 с тиші до кінця capture (642.21 с).

## Bugs / findings

Severity як зафіксовано в Task: 2 High. Усього defects: 2.

| ID | Defect | Severity | Reproducibility | Expected | Actual |
|---|---|---|---|---|---|
| T4-01 | Після першого NACK пристрій припиняє всю I2C-активність | High | 1/1 capture | Продовження опитування або повідомлення про помилку | NACK на 0x69 у 609.122546 с, далі 33.09 с без активності |
| T4-02 | Після NACK не видно recovery чи reboot | High (proposed) | 1/1 capture | Видимий recovery (retry, re-init 0x6B, reboot) | Жодного обміну з 0x68, жодного запису в 0x6B |

Повний реєстр усіх 36 defects — [bug-reports/BUG_REGISTER_UA.md](../../bug-reports/BUG_REGISTER_UA.md).

## Evidence

- [i2c_failure.sr](i2c_failure.sr) — capture (610 транзакцій, оригінальна назва home_work4.sr)
- [Protocol Analysis Sheet.xlsx](Protocol%20Analysis%20Sheet.xlsx), [Protocol_Analysis_Sheet_Test_Log_Webinar.pdf](Protocol_Analysis_Sheet_Test_Log_Webinar.pdf), [QA_Conclusion_I2C_trace_ESP32_MPU6050.pdf](QA_Conclusion_I2C_trace_ESP32_MPU6050.pdf)
- [screenshots/task4_protocol_analysis_sheet.png](screenshots/task4_protocol_analysis_sheet.png) — рендер PDF-звіту

Прогалини: один capture, немає serial log firmware, невідомо, коли FAULT вимкнено; пристрій навіть звертався до 0x69 замість 0x68.

## What I learned / decisions made

- Trace доводить факт тиші, але не доводить причину: потрібні serial log і момент вимкнення FAULT.
- Без вимог я сформулював очікування як припущення (retry або повідомлення про помилку).
- Рішення: повторити тест із FAULT off у відомий момент і зберегти log firmware.
