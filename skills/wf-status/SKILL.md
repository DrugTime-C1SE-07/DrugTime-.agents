---
name: wf-status
description: Cho biết một task đang ở đâu trong quy trình — suy task ID từ tên nhánh nếu không được nói, chạy gate.py, đọc mục Bước tiếp theo của các artifact, báo giai đoạn đã duyệt, đang chờ duyệt, approval đã cũ, câu hỏi còn mở và việc cần làm kế tiếp. Chỉ đọc, không sửa file. Use when the user asks "task đang ở đâu", "trạng thái task", "tới bước nào rồi", "status", "còn gì chưa xong", or when resuming work in a new session or another tool.
---

# Trạng thái task

## Vai trò

Người điều phối, chỉ đọc.

- **Chịu trách nhiệm**: người dùng biết chính xác task đang ở đâu và ai đang phải làm gì.
- **Mặc định**: tin `gate.py` và nội dung file, không tin trí nhớ hay lịch sử chat.
- **Không làm**: sửa file, bắt đầu giai đoạn nào.

## Các bước

1. Task ID: từ lời người dùng; nếu không có, `python .agents/scripts/gate.py current`. Nhiều task thì liệt kê và hỏi chọn.
2. `python .agents/scripts/gate.py <task-id>`: bảng trạng thái từng artifact và giai đoạn cần làm hoặc chờ duyệt.
3. Đọc mục "Bước tiếp theo" và "Câu hỏi mở" của artifact mới nhất; với `04-impl-notes.md`, đọc thêm bảng tiến độ.
4. `git status` ngắn ở superproject và các submodule trong `affected` của `01`: nhánh hiện tại, file chưa commit, `work/<task-id>/` đã commit chưa.
5. Trả lời trong 5–10 dòng:
   - giai đoạn hiện tại và trạng thái (draft, chờ duyệt, approved, approved nhưng đã cũ);
   - đang chờ ai (người duyệt, người dùng trả lời câu hỏi, agent);
   - việc cụ thể kế tiếp, kèm lệnh nếu có (`gate.py approve …` cho người duyệt, hoặc skill giai đoạn kế tiếp);
   - cảnh báo: approval đã cũ, file chưa commit, `owner` khác người đang làm.
