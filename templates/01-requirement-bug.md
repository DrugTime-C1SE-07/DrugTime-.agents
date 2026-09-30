---
task: <task-id>
title: <tiêu đề ngắn>
type: bug
severity: <Critical | High | Medium | Low>
stage: requirement
status: draft
size: <S | M | L>
contract_change: unknown
affected: []
---

# <task-id> · <tiêu đề>

## 1. Triệu chứng

- Mong đợi:
- Thực tế:
- Môi trường:
- Thông báo lỗi / log:

## 2. Tái hiện

| Lệnh / thao tác | Kết quả | Log |
|---|---|---|
|  |  | `evidence/requirement-repro.log` |

<Nếu không tái hiện được: đã thử gì, giả thuyết xếp theo khả năng, thông tin cần thêm.>

## 3. Nguyên nhân gốc

- Nguyên nhân gốc (hoặc "Giả thuyết:"):
- Chuỗi suy luận và bằng chứng (file:dòng, log, truy vấn):

## 4. Phạm vi ảnh hưởng

- Chỗ khác có cùng mẫu lỗi:
- Dữ liệu đã bị ảnh hưởng:
- Vùng rủi ro và bất biến bị chạm:

## 5. Submodule bị ảnh hưởng

| Submodule | Ảnh hưởng? | Lý do |
|---|---|---|
|  |  |  |

## 6. Hướng sửa đề xuất

| Hướng | Đánh đổi |
|---|---|
|  |  |

Đề xuất:

## 7. Thay đổi API contract

- `contract_change`: <yes | no | unknown>
- Lý do:

## 8. Tiêu chí chấp nhận (gồm test hồi quy)

| ID | Given / When / Then | Mức test |
|---|---|---|
| AC1 |  |  |

## 9. Câu hỏi mở

## 10. Giả định

## 11. Phát sinh

## 12. Size

- `size`: <S | M | L>
- Lý do:

<!-- Mục 13 và 14 chỉ điền khi size: S. Size M/L thì xóa hai mục này. -->

## 13. File sẽ thay đổi (chỉ task S)

| Submodule | Đường dẫn | Thêm / sửa / xóa | Mục đích |
|---|---|---|---|
|  |  |  |  |

## 14. Checklist (chỉ task S)

- [ ] P1 [<submodule>] Viết test hồi quy, xác nhận fail — file: <đường dẫn> — AC: AC1 — xong khi: test fail đúng như mô tả

## Bước tiếp theo

- Đang chờ: <người duyệt | người dùng trả lời Q… | agent>
- Việc cần làm: <ví dụ: người dùng trả lời Q1 rồi chạy `python .agents/scripts/gate.py approve <task-id> <giai-đoạn>`; hoặc agent tiếp tục từ P4>
- Cập nhật lần cuối: <YYYY-MM-DD HH:MM>, <tool>
