---
name: wf-implement
description: Giai đoạn 4 — dùng khi 03-plan.md đã approved (task size S thì khi 01 đã approved) và 04-impl-notes.md chưa có hoặc đang draft. Viết code đúng checklist đã duyệt, viết unit test kèm theo, chạy test, lưu log bằng chứng, ghi tiến độ vào work/<task-id>/04-impl-notes.md; không sửa file ngoài plan. Use when the user asks to implement, code, "bắt đầu code", "làm theo plan", "viết code cho task X" on a task with an approved plan, or to continue an implementation in progress.
---

# Implement (giai đoạn 4)

## Vai trò

Kỹ sư thực thi plan đã được duyệt.

- **Chịu trách nhiệm**: code đúng plan, có unit test, và tiến độ luôn được ghi lại để người khác tiếp tục được.
- **Ưu tiên khi mâu thuẫn**: đúng và an toàn > đúng phạm vi > theo pattern có sẵn > nhanh.
- **Mặc định**: người duyệt đồng ý với plan, không đồng ý với phiên bản agent tự sửa; thấy plan sai thì dừng và hỏi.
- **Không làm**: sửa file ngoài plan, "tiện tay" refactor, báo test pass khi chưa chạy.

## Các bước

### 1. Kiểm tra cổng và đọc đầu vào

`python .agents/scripts/gate.py <task-id> implement`; exit khác 0 thì dừng (kể cả khi lý do là `owner` khác người đang làm). Đọc `01`, `02` (nếu có), `03` (task S: bảng file và checklist nằm trong `01`).

`04-impl-notes.md` đã có ở `draft`: đây là phiên tiếp tục (có thể từ tool khác). Đọc bảng tiến độ và "Bước tiếp theo", tiếp tục từ bước chưa xong; không làm lại bước đã xong trừ khi test của nó đang fail.

### 2. Chuẩn bị git

Mỗi submodule sẽ sửa: theo `wf-git` (trạng thái, thoát detached HEAD, nhánh ghi trong plan). Có thay đổi chưa commit của người khác thì không đụng vào; dừng và hỏi.

### 3. Tạo `04-impl-notes.md` ngay từ đầu

Theo mẫu `.agents/templates/04-impl-notes.md`, `status: draft`, `owner` là `git config user.name`, `started_at` là thời điểm bắt đầu, bảng tiến độ gồm mọi bước ở trạng thái "chưa làm". Cập nhật sau mỗi bước. Tiến độ ghi ở đây, không tick trong plan đã duyệt.

### 4. Làm từng bước theo thứ tự

1. Chỉ sửa file thuộc bảng "File sẽ thay đổi", trừ file trong vùng `integration-test` (thuộc giai đoạn 5).
2. Theo pattern có sẵn (cấu trúc module, đặt tên, xử lý lỗi, logging) và quy tắc kiến trúc trong `AGENTS.md`.
3. Viết unit test của bước ngay trong bước đó.
4. Chạy test liên quan, lưu output vào `work/<task-id>/evidence/implement-<Pn>.log`, ghi lệnh, kết quả ngắn và đường dẫn log vào bảng tiến độ.
5. Đánh dấu xong chỉ khi điều kiện "xong khi" đã đạt.

Task bug: bước đầu là viết test hồi quy, chạy để xác nhận nó fail đúng như mô tả, lưu log, rồi mới sửa code.

Bước chạm schema hoặc endpoint dữ liệu sức khỏe: áp dụng `wf-db-migration` hoặc `wf-health-endpoint`.

### 5. Khi thực tế khác plan

Cần sửa file không có trong plan, đổi cách làm, hay một AC không đạt được như thiết kế: dừng. Ghi vào "Phát sinh" điều phát hiện, đề xuất thay đổi plan, và hỏi. Nếu người dùng đồng ý, họ chạy `gate.py reopen <task-id> plan` để cập nhật plan qua `wf-plan`. Không "tiện tay" sửa code không liên quan, đổi tên hàng loạt hay nâng cấp thư viện.

### 6. Chất lượng code

- Không hardcode secret, key, URL môi trường.
- Không nuốt lỗi: mọi `except`/`catch` hoặc xử lý cụ thể, hoặc ghi log và ném tiếp.
- Không để code chết, `print` debug, hoặc `TODO` không ghi chú trong `04-impl-notes.md`.
- Chạy formatter và linter mà `AGENTS.md` ghi.

### 7. Kiểm tra cuối

- Chạy toàn bộ unit test của mọi submodule đã sửa, lưu log `evidence/implement-final-<submodule>.log`, ghi số pass/fail. Test cũ fail vì thay đổi của task thì phải xử lý hoặc báo.
- `python .agents/scripts/scope.py <task-id> --stage implement`, lưu log. Có file `[NGOÀI]` thì xử lý theo bước 5 trước khi bàn giao.

### 8. Bàn giao và dừng

Hoàn thiện `04-impl-notes.md` (tiến độ, file đã đổi, test cuối, phát sinh, ghi chú cho reviewer, "Bước tiếp theo"). Không commit hay push nếu chưa được yêu cầu; nếu được, theo `wf-git`. Trả lời người dùng: số bước xong trên tổng, kết quả test, phát sinh, lệnh duyệt. Dừng ở đó.

## Tự kiểm trước khi bàn giao

- [ ] Mọi bước có trạng thái trong bảng tiến độ, bước xong có log.
- [ ] `scope.py --stage implement` không có file `[NGOÀI]`.
- [ ] Toàn bộ unit test đã chạy trong phiên này, có log.
- [ ] Task bug: có log chứng minh test hồi quy fail trước và pass sau khi sửa.
