---
task: <task-id>
stage: implement
status: draft
owner: <git config user.name của người đang làm>
started_at: <YYYY-MM-DD HH:MM>
---

# <task-id> · Implement

## 1. Tiến độ

| Bước | Trạng thái | Lệnh kiểm tra và kết quả | Log |
|---|---|---|---|
| P1 | chưa làm / đang làm / xong |  | `evidence/implement-P1.log` |

## 2. File đã thay đổi

| Submodule | Nhánh | File |
|---|---|---|
|  |  |  |

Kết quả `python .agents/scripts/scope.py <task-id> --stage implement`: <OK | danh sách file ngoài phạm vi> — log: `evidence/implement-scope.log`

## 3. Kết quả test cuối

| Submodule | Lệnh | Kết quả (pass/fail/skip) | Log |
|---|---|---|---|
|  |  |  | `evidence/implement-final-<submodule>.log` |

<Task bug: log chứng minh test hồi quy fail trước và pass sau khi sửa.>

## 3b. Bộ test case Excel (chỉ task size S)

<Theo skill wf-testcase: spec, file task, file tổng, số Pass/Fail/Pending theo chức năng, Pending cần người chạy, log `evidence/testcase-xlsx.log`. Task M/L ghi "Làm ở giai đoạn test".>

## 4. Migration

<Theo skill wf-db-migration. Không có thì ghi "Không có".>

## 5. Ghi chú cho người review

## 6. Phát sinh

## Bước tiếp theo

- Đang chờ: <người duyệt | người dùng trả lời Q… | agent>
- Việc cần làm: <ví dụ: agent tiếp tục từ P4; hoặc người duyệt chạy `python .agents/scripts/gate.py approve <task-id> implement`>
- Cập nhật lần cuối: <YYYY-MM-DD HH:MM>, <tool>
