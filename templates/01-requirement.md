---
task: <task-id>
title: <tiêu đề ngắn>
type: feature
stage: requirement
status: draft
size: <S | M | L>
contract_change: unknown
affected: []
---

# <task-id> · <tiêu đề>

## 1. Mục tiêu

<1–3 câu, theo góc nhìn người dùng hoặc hệ thống.>

## 2. Phạm vi

### Trong phạm vi

- 

### Ngoài phạm vi

- 

## 3. Bối cảnh & nguồn đã đọc

| Nguồn (đường dẫn) | Điều rút ra |
|---|---|
|  |  |

## 4. Submodule bị ảnh hưởng

| Submodule | Ảnh hưởng? | Lý do |
|---|---|---|
|  |  |  |

## 5. Thay đổi API contract

- `contract_change`: <yes | no | unknown>
- Lý do:
- Endpoint liên quan (thêm / sửa / xóa / chỉ dùng):

## 6. Vùng rủi ro và bất biến bị chạm

- 

## 7. Tiêu chí chấp nhận

| ID | Given / When / Then | Mức test |
|---|---|---|
| AC1 |  |  |

## 8. Câu hỏi mở

<Theo định dạng Q1 [chặn | không chặn] trong skill. Không có thì ghi "Không có".>

## 9. Giả định

- 

## 10. Phát sinh

<Điều phát hiện ngoài phạm vi task. Không có thì ghi "Không có".>

## 11. Size

- `size`: <S | M | L>
- Lý do:

<!-- Mục 12 và 13 chỉ điền khi size: S (task S không có 03-plan.md). Size M/L thì xóa hai mục này. -->

## 12. File sẽ thay đổi (chỉ task S)

| Submodule | Đường dẫn | Thêm / sửa / xóa | Mục đích |
|---|---|---|---|
|  |  |  |  |

## 13. Checklist (chỉ task S)

- [ ] P1 [<submodule>] <việc> — file: <đường dẫn> — AC: <AC> — xong khi: <điều kiện>

## Bước tiếp theo

- Đang chờ: <người duyệt | người dùng trả lời Q… | agent>
- Việc cần làm: <ví dụ: người dùng trả lời Q1 rồi chạy `python .agents/scripts/gate.py approve <task-id> <giai-đoạn>`; hoặc agent tiếp tục từ P4>
- Cập nhật lần cuối: <YYYY-MM-DD HH:MM>, <tool>
