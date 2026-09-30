---
name: wf-requirement
description: Giai đoạn 1 cho tính năng (không phải bug) — dùng khi work/<task-id>/01-requirement.md chưa có hoặc đang draft. Phân tích yêu cầu, task backlog, user story; tạo 01-requirement.md gồm phạm vi, size S/M/L, tiêu chí chấp nhận kiểm thử được, submodule bị ảnh hưởng, có đổi API contract hay không, câu hỏi mở. Use when the user starts a new feature, change or backlog item that has no approved requirement yet — e.g. "phân tích task 1.10", "phân tích yêu cầu", "thêm tính năng X", "build the login API" — even if they ask to start coding right away. If 01 is already approved, use wf-next. For bugs, errors and failing tests use wf-bug.
---

# Phân tích yêu cầu (giai đoạn 1)

## Vai trò

Business analyst của task.

- **Chịu trách nhiệm**: bản phân tích đủ rõ để người duyệt nói "đúng, làm cái này" và người viết test kiểm chứng được.
- **Ưu tiên khi mâu thuẫn**: đúng nhu cầu > rõ phạm vi > đầy đủ chi tiết.
- **Mặc định**: yêu cầu còn mơ hồ cho tới khi có tiêu chí kiểm chứng được; luôn hỏi "khi nào thì coi là sai".
- **Không làm**: thiết kế giải pháp kỹ thuật, viết code, hỏi điều mà repo đã trả lời.

Nếu người dùng muốn code ngay, giải thích ngắn rằng quy trình bắt đầu bằng bản phân tích được duyệt, rồi làm bản phân tích.

## Đầu vào

- Mô tả task từ người dùng, hoặc mã task trong sprint backlog. Với mã task, tìm mô tả trong tài liệu mà phần "Dự án" của `AGENTS.md` chỉ tới; dùng mục đích, các bước và tiêu chí hoàn thành đã có làm điểm xuất phát, không hỏi lại.
- Phần "Dự án" của `AGENTS.md`: cấu trúc repo, vai trò submodule, bất biến kiến trúc, vùng rủi ro, kịch bản chất lượng.

## Các bước

### 1. Kiểm tra cổng

Task ID theo quy ước trong `AGENTS.md`. Chạy `python .agents/scripts/gate.py <task-id> requirement`; exit khác 0 thì dừng và báo lý do. Nếu `01-requirement.md` đã có ở trạng thái `draft`, đây là vòng sửa: đọc và tiếp tục từ đó.

### 2. Tự tìm hiểu trước khi hỏi

Đọc code, contract và tài liệu liên quan; chỉ đọc. Mục tiêu: biết tính năng đã có một phần chưa, endpoint nào đang có, bảng dữ liệu nào liên quan, module nào sở hữu logic. Ghi mọi nguồn đã đọc vào mục "Bối cảnh & nguồn đã đọc" để agent sau (có thể trên tool khác) không phải đọc lại. Câu hỏi trả lời được bằng cách đọc repo thì không hỏi.

### 3. Mục tiêu và phạm vi

Mục tiêu một đến ba câu, theo góc nhìn người dùng cuối hoặc hệ thống. Liệt kê rõ "ngoài phạm vi"; đây là chỗ ngăn phạm vi phình ra và là thứ người duyệt hay bỏ sót nhất.

### 4. Submodule bị ảnh hưởng

Với mỗi submodule, ghi có bị ảnh hưởng không và vì sao. Điền trường `affected` của frontmatter, ví dụ `affected: [backend, api_contract, tests]`.

### 5. `contract_change`

Quyết định dựa trên hành vi của API, không dựa trên việc task có "làm frontend" hay không.

- `yes` khi thêm, sửa hoặc xóa điều mà client đang dùng hoặc sẽ dùng: endpoint (đường dẫn, method); field request hoặc response (tên, kiểu, bắt buộc, ý nghĩa); mã trạng thái, định dạng lỗi, yêu cầu xác thực.
- `no` khi mọi thay đổi nằm sau API và hình dạng API giữ nguyên, hoặc client chỉ dùng endpoint có sẵn. Trường hợp sau vẫn ghi rõ dùng endpoint nào.

Task "chỉ backend" vẫn có thể là `yes`. Chưa quyết được thì để `unknown` kèm một câu hỏi "chặn"; `gate.py` không cho sang giai đoạn sau khi còn `unknown`.

### 6. Vùng rủi ro

Đối chiếu vùng rủi ro và bất biến trong `AGENTS.md`. Chỉ ghi vùng thực sự bị chạm; liệt kê tràn lan làm người duyệt bỏ qua cả mục.

### 7. Xếp size

| Size | Tiêu chí |
|---|---|
| S | Không chạm vùng rủi ro nào ở bước 6, `contract_change: no`, khoảng 3 file và 50 dòng trở xuống |
| M | Còn lại, trong một đến hai submodule |
| L | Nhiều submodule, hoặc cần migration, hoặc đổi contract phá vỡ |

Không chắc giữa hai mức thì chọn mức lớn hơn. Với size S, điền thêm mục "File sẽ thay đổi" và "Checklist" của mẫu (cùng định dạng với `03-plan.md`); task S không có giai đoạn plan và test tích hợp.

### 8. Tiêu chí chấp nhận

Dạng Given / When / Then, kiểm chứng được bằng một test cụ thể, gắn mức test:

- `unit`: kiểm được trong một module, không cần DB thật.
- `integration`: cần API chạy cùng DB.
- `manual`: chỉ kiểm được bằng tay (ví dụ trên thiết bị thật); ghi lý do.

Có ít nhất một tiêu chí cho đường thành công và một cho đường lỗi hoặc bị từ chối. Task chạm vùng rủi ro thì thêm tiêu chí ứng với kịch bản chất lượng của dự án.

Tốt: "Given người thân không có liên kết với patient, When gọi GET lịch sử liều của patient đó, Then trả 403 và có một dòng log `denied`." Kém: "Phân quyền hoạt động đúng."

### 9. Câu hỏi mở

Tối đa 5 câu, mỗi câu phải làm thay đổi thiết kế hoặc tiêu chí nếu câu trả lời khác đi:

```
Q1 [chặn | không chặn] <câu hỏi>
- Ảnh hưởng: <điều gì thay đổi tùy câu trả lời>
- Lựa chọn: <A> / <B>
- Giả định mặc định: <lựa chọn agent sẽ theo nếu người dùng chỉ xác nhận>
```

### 10. Ghi artifact và dừng

Tạo `work/<task-id>/01-requirement.md` theo mẫu `.agents/templates/01-requirement.md`, `status: draft`, điền mục "Bước tiếp theo". Trả lời người dùng: đường dẫn file, tóm tắt 3–5 dòng, `size`, `contract_change`, câu hỏi mở, và lệnh duyệt `python .agents/scripts/gate.py approve <task-id> requirement`. Dừng ở đó.

Khi người dùng trả lời câu hỏi: cập nhật file (vẫn `draft`), chuyển câu đã trả lời sang "Giả định" hoặc sửa nội dung tương ứng, nói rõ đã đổi gì.

## Tự kiểm trước khi bàn giao

- [ ] Mọi mục của mẫu có nội dung, hoặc ghi "Không có" kèm lý do.
- [ ] `contract_change` là `yes`/`no` có lý do, hoặc `unknown` kèm câu hỏi "chặn".
- [ ] `size` có lý do; task S không chạm vùng rủi ro và có bảng "File sẽ thay đổi".
- [ ] Mỗi tiêu chí chấp nhận có mức test và kiểm chứng được.
- [ ] `python .agents/scripts/scope.py <task-id> --stage requirement` không báo file ngoài phạm vi.
