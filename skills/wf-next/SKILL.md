---
name: wf-next
description: Điểm vào duy nhất cho câu "làm task X" khi không nói rõ giai đoạn — xác định task ID (từ lời người dùng hoặc tên nhánh), dùng gate.py tìm giai đoạn kế tiếp được phép chạy, rồi đọc và làm đúng skill của giai đoạn đó (wf-requirement hoặc wf-bug, wf-contract, wf-plan, wf-implement, wf-test, wf-review). Use when the user says "làm task 1.10", "tiếp tục task", "làm bước tiếp theo", "next", "continue", "implement task X" without naming a stage, or when unsure which stage skill applies.
---

# Làm giai đoạn kế tiếp

## Vai trò

Người điều phối.

- **Chịu trách nhiệm**: chọn đúng một giai đoạn được phép chạy và giao cho đúng skill.
- **Mặc định**: `gate.py` quyết định giai đoạn, không đoán theo câu chữ của người dùng.
- **Không làm**: chạy nhiều giai đoạn trong một lượt, duyệt thay người, lách cổng.

## Các bước

1. Task ID: từ lời người dùng; nếu không có, `python .agents/scripts/gate.py current`. Không có `work/<task-id>/` → đây là giai đoạn 1: bug thì `wf-bug`, còn lại `wf-requirement`.
2. `python .agents/scripts/gate.py <task-id>`: đọc dòng "Giai đoạn cần làm hoặc chờ duyệt".
3. Với giai đoạn đó:
   - artifact chưa có, hoặc đang `draft` → đọc và làm theo skill của giai đoạn (bảng ở core §1), bắt đầu từ bước kiểm tra cổng của skill;
   - artifact đang `draft` và đã xong theo tự kiểm của skill, chỉ chờ duyệt → không làm gì thêm; nhắc người dùng đọc và chạy `python .agents/scripts/gate.py approve <task-id> <giai-đoạn>`;
   - approval đã cũ → báo artifact nào cần duyệt lại và vì sao;
   - không còn giai đoạn nào → báo task đã xong quy trình; gợi ý bước PR theo `wf-git`.
4. Dừng khi skill của giai đoạn đó dừng. Không tự chuyển sang giai đoạn sau.
