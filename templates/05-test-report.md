---
task: <task-id>
stage: test
status: draft
---

# <task-id> · Test tích hợp

## 1. Môi trường

- Lệnh chuẩn bị (reset DB, khởi động service):
- Nhánh của vùng test tích hợp:

## 2. Kết quả theo tiêu chí chấp nhận

| AC | Test | Kết quả |
|---|---|---|
|  |  | pass / fail |

## 3. Kịch bản chất lượng đã phủ

| Kịch bản | Test | Kết quả |
|---|---|---|
|  |  |  |

## 4. Toàn bộ bộ test tích hợp

- Lệnh:
- Kết quả: <pass / fail / skip / thời gian>
- Log: `evidence/test-integration.log`
- `scope.py --stage test`: <OK | file ngoài phạm vi>

## 5. Lỗi sản phẩm tìm thấy

<Test, kỳ vọng, thực tế, nghi vấn nguyên nhân. Không có thì ghi "Không có".>

## 6. Test không ổn định hoặc bị skip

## 7. Phát sinh

## Bước tiếp theo

- Đang chờ: <người duyệt | người dùng | agent>
- Việc cần làm: <ví dụ: người duyệt chạy `python .agents/scripts/gate.py approve <task-id> test`; hoặc reopen implement vì lỗi sản phẩm>
- Cập nhật lần cuối: <YYYY-MM-DD HH:MM>, <tool>
