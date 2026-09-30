---
name: wf-test
description: Giai đoạn 5 — dùng khi 04-impl-notes.md đã approved và 05-test-report.md chưa có hoặc đang draft (task size S không có giai đoạn này). Viết và chạy test tích hợp cho tiêu chí chấp nhận mức integration và kịch bản chất lượng của dự án (phân quyền, rút quyền, audit log, idempotency, chạy đua), chạy lại toàn bộ bộ test, tạo work/<task-id>/05-test-report.md. Use when the user asks for integration tests, end-to-end API tests, "viết test tích hợp", "kiểm thử task", "test report".
---

# Test tích hợp (giai đoạn 5)

## Vai trò

QA của task.

- **Chịu trách nhiệm**: chứng minh bằng test chạy thật rằng mọi tiêu chí chấp nhận và kịch bản chất lượng được đáp ứng.
- **Ưu tiên khi mâu thuẫn**: phủ vùng rủi ro > phủ tiêu chí chấp nhận > số lượng test.
- **Mặc định**: tìm cách làm hệ thống sai, không chỉ xác nhận đường thành công.
- **Không làm**: sửa code sản phẩm, skip hay nới lỏng test để nó pass.

Test tích hợp bám theo tiêu chí chấp nhận và contract, không bám chi tiết cài đặt. Chỉ sửa trong vùng `integration-test` ghi ở mục "Vai trò submodule" của `AGENTS.md`.

## Các bước

### 1. Kiểm tra cổng và đọc đầu vào

`python .agents/scripts/gate.py <task-id> test`; exit khác 0 thì dừng. Đọc `01` (AC mức `integration`, vùng rủi ro), `02` (nếu có), danh sách test tích hợp trong `03`, và `04`.

Đọc "Kịch bản chất lượng cho test tích hợp" trong `AGENTS.md`. Kịch bản ứng với vùng rủi ro mà task chạm là bắt buộc, kể cả khi plan quên liệt kê.

### 2. Tìm hiểu bộ test hiện có

Trong vùng `integration-test`: cấu trúc, fixture, cách tạo dữ liệu, cách khởi động API và DB, lệnh chạy. Dùng lại fixture và helper. Chuẩn bị nhánh theo `wf-git`.

### 3. Chuẩn bị môi trường

Reset DB sạch và khởi động service theo lệnh trong `AGENTS.md`. Ghi lệnh. Không chạy test tích hợp lên môi trường deploy hay DB dùng chung.

### 4. Viết test

- **Độc lập**: mỗi test tự tạo dữ liệu, không phụ thuộc thứ tự chạy hay dữ liệu test khác để lại.
- **Theo contract**: khẳng định mã trạng thái, schema và giá trị như trong contract.
- **Kiểm hiệu ứng phụ trong DB** khi AC yêu cầu: số bản ghi, trạng thái, dòng audit log.
- **Tất định**: không `sleep` để chờ, không phụ thuộc giờ thật; dùng mốc thời gian cố định hoặc cơ chế điều khiển thời gian có sẵn.
- **Tên theo hành vi**, kèm mã AC, ví dụ `test_unlinked_caregiver_gets_403_and_denied_log__AC3`.

Kịch bản đặc thù:

- **Phân quyền**: luôn có cặp "được phép" và "bị từ chối" cho cùng endpoint; với bị từ chối, kiểm cả response lẫn dòng log từ chối.
- **Rút quyền**: rút quyền rồi gửi request ngay, kỳ vọng bị từ chối.
- **Idempotency**: gửi cùng request (cùng khóa) hai lần, kỳ vọng đúng một bản ghi.
- **Chạy đua**: gửi thao tác xung đột đồng thời, kiểm trạng thái cuối không trùng và không ghi đè sai.

### 5. Chạy

Chạy test mới, rồi **toàn bộ** bộ test tích hợp. Lưu output vào `work/<task-id>/evidence/test-integration.log`; ghi lệnh, số pass/fail/skip, thời gian.

### 6. Xử lý test fail

- **Lỗi của test** (dữ liệu, fixture, khẳng định sai): sửa test.
- **Lỗi của sản phẩm**: không sửa code sản phẩm. Ghi test, kỳ vọng, thực tế, nghi vấn nguyên nhân. Người dùng sẽ `gate.py reopen <task-id> implement`.
- **Không ổn định**: chạy lại vài lần để xác nhận, ghi số lần; không che bằng tăng retry hay timeout.

Không xóa, skip hay nới lỏng khẳng định để test pass.

### 7. Ghi artifact và dừng

`python .agents/scripts/scope.py <task-id> --stage test`. Tạo `work/<task-id>/05-test-report.md` theo mẫu `.agents/templates/05-test-report.md`, `status: draft`, điền "Bước tiếp theo". Trả lời người dùng: bảng AC → test → kết quả, kịch bản chất lượng đã phủ, lỗi sản phẩm tìm thấy, lệnh duyệt. Dừng ở đó.

## Tự kiểm trước khi bàn giao

- [ ] Mọi AC mức `integration` có ít nhất một test; mọi kịch bản chất lượng áp dụng đã được phủ.
- [ ] Toàn bộ bộ test tích hợp đã chạy trong phiên này, có log.
- [ ] Không test nào bị skip hay nới lỏng mà không ghi lý do.
- [ ] `scope.py --stage test` không báo file ngoài phạm vi.
