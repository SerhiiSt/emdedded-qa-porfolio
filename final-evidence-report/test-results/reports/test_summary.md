# Test Summary — Embedded QA (Tasks 1–7)

Підсумковий звіт: покриття, кількість тестів, результати. Дані з `test-results/` і `logs/`.

## Автоматизовані набори

| Task | Suite | Total | Passed | Failed | Skipped | Інше | Час |
|---|---|---|---|---|---|---|---|
| 2 | Wokwi CLI scenarios (`verdicts.md`) | 38 | 28 | 7 | 0 | 2 REVIEW, 1 INVALID (TC-24 timed out) | — |
| 5 | pytest (`pytest_log_task5.pdf`) | 49 | 18 | 26 | 4 | 1 error | 467.53 с |
| 6 | pytest (`pytest_output.txt`) | 96 | 72 | 17 | 2 | 4 xfailed, 1 error | 623.14 с |
| 7 | pytest, manual scenarios | 22 | 16 | 5 | 1 | — | 264.84 с |
| 7 | pytest, recommendations suite | 27 | 5 | 22 | 0 | — | 520.01 с |
| **Разом** | | **232** | **139** | **77** | **7** | 4 xfailed, 2 errors, 2 REVIEW, 1 INVALID | |

Pass rate: 139 / 232 = **59.9%**. OVERALL: **FAIL** (відкриті Blocker / Critical defects).

Примітки:
- Failed включає тести, написані для виявлення підозрілого bug (bug candidates), і не дорівнює кількості defects (36).
- Task 3: 36 сценаріїв Wokwi CLI (TC-01…TC-36, `logs/task3_uart_cli/`) — окремі pass / fail підсумки не витягувались; знайдено 5 defects.
- Tasks 1 і 4: ручне виконання (xlsx / analysis sheet), 12 і 2 defects.

## Defects

Усього 36: 5 Blocker, 4 Critical, 13 Major, 4 High, 3 Medium, 6 Minor / Low / Trivial, 1 без severity (T1-07). Реєстр — Appendix A у `master-test-plan.md`.

## Exit Criteria

Не виконані: 9 відкритих Blocker / Critical defects, regression не виконувався, recovery не підтверджено (powerloss, watchdog, NACK, мережа). Рішення: **NO-GO**.
