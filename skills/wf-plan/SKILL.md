---
name: wf-plan
description: Giai đoạn 3 — dùng khi 01-requirement.md (và 02-contract.md nếu có) đã approved và 03-plan.md chưa có hoặc đang draft. Lập kế hoạch kỹ thuật gồm file sẽ sửa theo submodule, checklist bước nhỏ kiểm chứng được gắn với tiêu chí chấp nhận, danh sách unit test và test tích hợp, rủi ro; tạo work/<task-id>/03-plan.md. Use when the user asks to plan, design the implementation, "lập kế hoạch", "lên plan", "thiết kế giải pháp", "chia nhỏ task". Not for size S tasks, which carry their plan inside 01.
---

# Lập kế hoạch (giai đoạn 3)

## Vai trò

Tech lead của task.

- **Chịu trách nhiệm**: plan chia nhỏ, kiểm chứng được từng bước, và là ranh giới phạm vi cho giai đoạn implement.
- **Ưu tiên khi mâu thuẫn**: bất biến kiến trúc > tái sử dụng cái có sẵn > đơn giản > tối ưu.
- **Mặc định**: chọn cách ít thay đổi nhất đáp ứng đủ tiêu chí chấp nhận; nêu rủi ro trước khi bị hỏi.
- **Không làm**: viết code, để lại bước mơ hồ kiểu "xử lý logic".

Bảng "File sẽ thay đổi" được `scope.py` đọc để chặn implement sửa ngoài phạm vi, nên phải đủ và đúng định dạng.

## Các bước

### 1. Kiểm tra cổng và đọc đầu vào

`python .agents/scripts/gate.py <task-id> plan`; exit khác 0 thì dừng. Đọc `01` và `02` (nếu có). Mọi tiêu chí chấp nhận (AC) phải được plan phủ.

### 2. Khảo sát code

Đọc phần code bị ảnh hưởng: module sở hữu logic, các lớp theo kiến trúc ghi trong `AGENTS.md`, pattern đang dùng cho việc tương tự, test hiện có. Ưu tiên tái sử dụng. Ghi file đã đọc vào mục "Khảo sát".

### 3. Skill chuyên đề

- Schema hoặc migration → `wf-db-migration`.
- Endpoint đọc hoặc ghi dữ liệu sức khỏe → `wf-health-endpoint`.

Yêu cầu của skill chuyên đề phải thành bước checklist và test cụ thể, không chỉ ghi "tuân thủ skill X".

### 4. Thiết kế giải pháp

Luồng dữ liệu, thành phần mới hoặc thay đổi, lý do chọn. Có hơn một cách hợp lý thì nêu cách chọn và vì sao bỏ cách kia, vài dòng. Đối chiếu bất biến trong `AGENTS.md`; giải pháp vi phạm bất biến thì không đề xuất mà nêu thành câu hỏi.

### 5. Bảng "File sẽ thay đổi"

Cột bắt buộc: `Submodule | Đường dẫn | Thêm / sửa / xóa | Mục đích`. Đường dẫn tính từ gốc submodule; được dùng glob khi tạo nhiều file mới trong một thư mục (`src/<module>/auth/**`). Gồm cả file test. File không có ở đây thì implement phải dừng lại hỏi.

### 6. Checklist

Mỗi bước là một thay đổi nhỏ, kiểm chứng được ngay, theo thứ tự thực hiện được:

```
- [ ] P1 [<submodule>] <việc cần làm> — file: <đường dẫn> — AC: AC1, AC2 — xong khi: <điều kiện kiểm chứng>
```

Thứ tự thường gặp: migration → lớp dữ liệu → logic → API → test → client. Với bug: bước đầu là viết test hồi quy và xác nhận nó fail.

### 7. Danh sách test

- **Unit**: theo từng bước; mỗi hàm logic có nhánh thành công, nhánh lỗi và giá trị biên.
- **Tích hợp**: mỗi AC mức `integration`, cộng kịch bản chất lượng trong `AGENTS.md` ứng với vùng rủi ro bị chạm. Ghi file nằm trong vùng `integration-test` của `AGENTS.md`.

Mỗi test ghi tên dự kiến, AC phủ, nơi chứa.

### 8. Nhánh git

Tên nhánh cho từng submodule theo `wf-git`.

### 9. Rủi ro

Điều có thể sai và cách phát hiện hoặc giảm thiểu: thay đổi dữ liệu không đảo ngược được, ảnh hưởng client đang chạy, hiệu năng truy vấn mới.

### 10. Ghi artifact và dừng

Tạo `work/<task-id>/03-plan.md` theo mẫu `.agents/templates/03-plan.md`, `status: draft`, điền "Bước tiếp theo". Trả lời người dùng: tóm tắt giải pháp, số file theo submodule, số bước, rủi ro chính, câu hỏi mở, lệnh duyệt. Dừng ở đó.

## Tự kiểm trước khi bàn giao

- [ ] Mọi AC được ít nhất một bước và một test phủ.
- [ ] Mọi file sẽ sửa, kể cả test, có trong bảng; bảng đúng bốn cột trên.
- [ ] Yêu cầu của skill chuyên đề đã thành bước và test cụ thể.
- [ ] Không có bước mơ hồ kiểu "xử lý logic" hay "cập nhật cho phù hợp".
- [ ] `python .agents/scripts/scope.py <task-id> --stage plan` không báo file ngoài phạm vi.
