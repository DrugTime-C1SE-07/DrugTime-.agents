---
name: wf-handoff
description: Chuẩn bị bàn giao task cho phiên khác, tool khác hoặc người khác — cập nhật tiến độ và mục Bước tiếp theo trong artifact đang làm, liệt kê file chưa commit ở superproject và submodule, soạn sẵn lệnh commit work/<task-id>/ và code đang dở. Use when the user says "tạm dừng", "bàn giao", "handoff", "chuyển sang máy khác", "để người khác làm tiếp", "lưu lại tiến độ", or before ending a session with unfinished work.
---

# Bàn giao task

## Vai trò

Người ghi biên bản bàn giao.

- **Chịu trách nhiệm**: người nhận chỉ cần đọc `work/<task-id>/` là làm tiếp được, trên bất kỳ tool hay máy nào.
- **Mặc định**: người nhận không có lịch sử chat của phiên này.
- **Không làm**: commit hay push khi người dùng chưa đồng ý, đổi trạng thái duyệt.

## Các bước

1. Task ID và giai đoạn hiện tại: `python .agents/scripts/gate.py` (hoặc `gate.py <task-id>`).
2. Cập nhật artifact đang làm (vẫn `draft`):
   - `04-impl-notes.md`: trạng thái từng bước; bước đang dở ghi rõ đã làm tới đâu và còn gì.
   - Mục "Bước tiếp theo": đang chờ ai, việc cần làm, thời điểm và tool cập nhật.
   - Quyết định hay phát hiện chỉ nằm trong chat thì chép vào "Giả định" hoặc "Phát sinh".
3. Liệt kê thay đổi chưa commit: `git status --short` ở superproject và các submodule trong `affected`.
4. Nếu người nhận là người khác và giai đoạn là implement: nhắc người dùng đổi `owner` trong `04-impl-notes.md` sang người nhận.
5. Soạn lệnh commit và push, theo `wf-git`, nhưng chỉ chạy khi người dùng đồng ý:
   - code dở trong submodule: commit trên nhánh task (message `wip: ...` được chấp nhận), push;
   - `work/<task-id>/` (trừ `scratch/`) trên nhánh task của superproject.
6. Trả lời: tóm tắt bàn giao 3–5 dòng, danh sách lệnh đã soạn, và câu người nhận nên gõ để tiếp tục (ví dụ `/wf-next <task-id>`).
