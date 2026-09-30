---
task: <task-id>
stage: plan
status: draft
---

# <task-id> · Plan

## 1. Giải pháp

<Luồng dữ liệu, thành phần thay đổi, lý do chọn cách này.>

## 2. Khảo sát

| File đã đọc | Điều rút ra |
|---|---|
|  |  |

## 3. File sẽ thay đổi (ranh giới phạm vi)

<!-- scope.py đọc bảng này. Đường dẫn tính từ gốc submodule; được dùng glob, ví dụ `src/<module>/auth/**`. -->

| Submodule | Đường dẫn | Thêm / sửa / xóa | Mục đích |
|---|---|---|---|
|  |  |  |  |

## 4. Checklist

- [ ] P1 [<submodule>] <việc> — file: <đường dẫn> — AC: <AC> — xong khi: <điều kiện>

## 5. Test

### Unit

| Test dự kiến | AC | Submodule |
|---|---|---|
|  |  |  |

### Tích hợp

| Test dự kiến | AC / kịch bản chất lượng | Ghi chú |
|---|---|---|
|  |  |  |

## 6. Migration

<Theo skill wf-db-migration. Không có thì ghi "Không có".>

## 7. Nhánh git

| Submodule | Nhánh |
|---|---|
|  |  |

## 8. Rủi ro

## 9. Câu hỏi mở

## 10. Phát sinh

## Bước tiếp theo

- Đang chờ: <người duyệt | người dùng trả lời Q… | agent>
- Việc cần làm: <ví dụ: người dùng trả lời Q1 rồi chạy `python .agents/scripts/gate.py approve <task-id> <giai-đoạn>`; hoặc agent tiếp tục từ P4>
- Cập nhật lần cuối: <YYYY-MM-DD HH:MM>, <tool>
