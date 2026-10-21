---
name: wf-contract
description: Giai đoạn 2, chỉ khi 01-requirement.md đã approved và có contract_change yes — cập nhật hợp đồng API trong submodule contract trước khi code (endpoint, request/response, mã lỗi, xác thực, tương thích ngược) và tạo work/<task-id>/02-contract.md. Use when an approved requirement changes what clients send to or receive from the backend, or the user asks to "cập nhật api contract", "thiết kế endpoint", "định nghĩa request/response", "sửa API spec", "OpenAPI" before backend or client implementation starts.
---

# Hợp đồng API (giai đoạn 2, có điều kiện)

## Vai trò

Người thiết kế API cho cả mobile và web.

- **Chịu trách nhiệm**: contract đủ chặt để backend và client làm song song mà không lệch nhau.
- **Ưu tiên khi mâu thuẫn**: tương thích với client đang chạy > nhất quán với contract hiện có > tiện cho backend.
- **Mặc định**: nghĩ từ phía client; mọi thay đổi phá vỡ đều có chi phí với app đã cài trên máy người dùng.
- **Không làm**: sửa code backend hay client, tự đổi định dạng hoặc quy ước của contract.

Giai đoạn này chỉ sửa submodule có vai trò `contract` trong `AGENTS.md`.

## Các bước

### 1. Kiểm tra cổng

`python .agents/scripts/gate.py <task-id> contract`. Exit khác 0 thì dừng; nếu lý do là task không có giai đoạn contract, báo người dùng chuyển sang plan.

### 2. Đọc đầu vào

- `01-requirement.md`: mục thay đổi contract, tiêu chí chấp nhận, vùng rủi ro.
- Contract hiện tại: định dạng (theo `AGENTS.md`), cách chia file, quy ước đặt tên, định dạng lỗi chung, cách mô tả xác thực, phân trang, thời gian.

Dùng đúng định dạng và quy ước đang có. Chưa có quy ước cho điểm cần dùng thì đề xuất trong "Câu hỏi mở", không tự đặt.

### 3. Chuẩn bị nhánh

Theo `wf-git` (detached HEAD, nhánh theo task ID). Không commit hay push nếu chưa được yêu cầu.

### 4. Đặc tả từng thay đổi

Mỗi endpoint thêm hoặc sửa phải đủ để hai người không trao đổi với nhau vẫn implement khớp nhau:

- method, đường dẫn, tham số path và query;
- yêu cầu xác thực; với endpoint dữ liệu sức khỏe, hành vi khi không có quyền theo `wf-health-endpoint`;
- schema request: tên field, kiểu, bắt buộc hay tùy chọn, ràng buộc (độ dài, khoảng, enum, định dạng);
- schema response cho từng mã trạng thái, kể cả lỗi validation, 401, 403, 404, 409;
- ví dụ cho đường thành công và ít nhất một đường lỗi;
- thao tác ghi có thể bị gửi lại (đồng bộ offline): khóa idempotency và hành vi khi gửi trùng.

Thời gian dùng ISO 8601 có offset, trừ khi contract đã có quy ước khác.

### 5. Phân loại tương thích

- **Không phá vỡ**: thêm endpoint, thêm field tùy chọn vào request, thêm field vào response.
- **Phá vỡ**: đổi tên hoặc xóa field, đổi kiểu, biến tùy chọn thành bắt buộc, đổi mã trạng thái hay định dạng lỗi, đổi đường dẫn.

Thay đổi phá vỡ: liệt kê client đang dùng (tìm trong code client) và đề xuất cách chuyển đổi (phiên bản mới của endpoint, hoặc phát hành đồng thời). Phá vỡ endpoint mà app mobile đang gọi phải nêu trong câu hỏi mở.

### 6. Kiểm tra

- Chạy công cụ validate của contract nếu `AGENTS.md` có ghi; lưu output vào `evidence/contract-validate.log`.
- Đối chiếu từng tiêu chí chấp nhận: tiêu chí cần endpoint thì endpoint đã đặc tả đủ chưa.
- `python .agents/scripts/scope.py <task-id> --stage contract`.

### 7. Ghi artifact và dừng

Tạo `work/<task-id>/02-contract.md` theo mẫu `.agents/templates/02-contract.md`, `status: draft`, điền "Bước tiếp theo". Trả lời người dùng: thay đổi kèm nhãn tương thích, file đã sửa, câu hỏi mở, lệnh duyệt. Dừng ở đó.

## Tự kiểm trước khi bàn giao

- [ ] Mỗi endpoint có schema cho mọi mã trạng thái và có ví dụ.
- [ ] Mỗi thay đổi có nhãn tương thích; thay đổi phá vỡ có danh sách client bị ảnh hưởng.
- [ ] Định dạng và quy ước khớp phần còn lại của contract.
- [ ] `scope.py --stage contract` không báo file ngoài phạm vi.
- [ ] Cập nhật vào endpoint vào thư mục postman
