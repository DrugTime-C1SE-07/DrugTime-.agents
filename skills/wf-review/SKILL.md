---
name: wf-review
description: Giai đoạn 6 — dùng khi 05-test-report.md đã approved (task size S thì khi 04 đã approved) và 06-review.md chưa có hoặc đang draft. Review độc lập toàn bộ diff của task trên mọi submodule theo tiêu chí chấp nhận, phạm vi, bất biến kiến trúc, bảo mật, dữ liệu và chất lượng test; phân loại Critical/High/Medium/Low, soạn mô tả PR, tạo work/<task-id>/06-review.md. Use when the user asks to review a task before merge, "review task", "kiểm tra trước khi merge", "soạn mô tả PR".
---

# Review (giai đoạn 6)

## Vai trò

Reviewer độc lập của task.

- **Chịu trách nhiệm**: không để lỗi Critical hoặc High lọt qua PR.
- **Ưu tiên khi mâu thuẫn**: đúng và an toàn > đúng phạm vi > dễ đọc > phong cách.
- **Mặc định**: code có lỗi cho tới khi thấy bằng chứng ngược lại; không tin mô tả trong artifact nếu chưa đối chiếu với diff và log.
- **Không làm**: sửa code, kết luận "Đạt" khi chưa đọc hết diff.

Skill này không thay thế người review PR theo Definition of Done; nó giúp người review tập trung vào chỗ đáng xem. Nên chạy trong phiên mới, tốt nhất trên tool khác với tool đã implement.

## Các bước

### 1. Kiểm tra cổng

`python .agents/scripts/gate.py <task-id> review`; exit khác 0 thì dừng.

### 2. Đọc yêu cầu, chưa đọc phần tự thuật

Đọc `01` (AC, vùng rủi ro), `02` (nếu có) và bảng file, checklist trong `03` (task S: trong `01`). **Chưa** đọc `04` và `05`, để không bị câu chuyện của người implement dẫn dắt.

### 3. Đọc toàn bộ diff và ghi phát hiện độc lập

Mỗi submodule bị ảnh hưởng: `git -C <submodule> diff <nhánh-gốc>...HEAD` (nhánh gốc trong `.gitmodules`). Đọc toàn bộ diff. Chạy `python .agents/scripts/scope.py <task-id> --stage implement`.

Ghi phát hiện kèm `file:dòng` cho từng mục:

1. **Đúng yêu cầu**: mỗi AC được code thực sự đáp ứng.
2. **Phạm vi**: kết quả `scope.py`; mọi lệch đã được ghi ở "Phát sinh" và được đồng ý.
3. **Contract**: response thực tế khớp contract (field, kiểu, mã trạng thái, định dạng lỗi).
4. **Bất biến kiến trúc**: từng bất biến trong `AGENTS.md` mà task chạm; checklist của `wf-health-endpoint` và `wf-db-migration` khi áp dụng.
5. **Bảo mật**: secret trong code hoặc log; dữ liệu nhạy cảm trong log; truy vấn ghép chuỗi; thiếu kiểm tra quyền; tin dữ liệu client mà không kiểm.
6. **Xử lý lỗi**: lỗi bị nuốt; thông báo lộ chi tiết nội bộ; thao tác nhiều bước thiếu transaction.
7. **Hiệu năng hiển nhiên**: N+1, truy vấn mới thiếu index, tải toàn bộ bảng.
8. **Chất lượng test**: khẳng định có ý nghĩa; có đường lỗi và từ chối; không skip vô lý do.
9. **Dễ đọc và nhất quán**: theo pattern có sẵn; không code chết, `print` debug, `TODO` không ghi chú.

### 4. Đối chiếu với tự thuật và bằng chứng

Giờ mới đọc `04` và `05`. So bảng kết quả với log trong `work/<task-id>/evidence/`: số pass/fail khớp không, có test nào fail hay skip bị bỏ qua không. Điều artifact nói mà diff hay log không chứng minh được là một phát hiện.

### 5. Phân loại

- **Critical**: vi phạm bất biến kiến trúc, lộ dữ liệu, sai quyền, mất hoặc hỏng dữ liệu.
- **High**: AC không đạt, lỗi logic trên luồng chính, thiếu test cho vùng rủi ro, kết quả test không khớp log.
- **Medium**: xử lý lỗi yếu, hiệu năng, lệch pattern đáng kể.
- **Low**: đặt tên, trình bày, gợi ý nhỏ.

### 6. Kết luận

- Có Critical hoặc High → **Chưa đạt**; người dùng `gate.py reopen` giai đoạn cần làm lại (thường là implement).
- Chỉ Medium hoặc Low → **Đạt, kèm lưu ý**.
- Không có phát hiện → **Đạt**.

### 7. Mô tả PR

Với "Đạt" hoặc "Đạt, kèm lưu ý": mô tả PR cho từng submodule và cho superproject (PR bump con trỏ): task ID, tóm tắt, AC và test chứng minh, cách test lại bằng tay (nếu có AC `manual`), rủi ro, liên kết giữa các PR, thứ tự merge theo `wf-git`.

### 8. Ghi artifact và dừng

Tạo `work/<task-id>/06-review.md` theo mẫu `.agents/templates/06-review.md`, `status: draft`. Điền "Ghi chú cho quy trình" nếu thấy skill chưa rõ hoặc agent trước đã mắc lỗi lặp lại. Trả lời người dùng: kết luận, số phát hiện theo mức, các phát hiện Critical/High, lệnh duyệt. Không mở PR hay merge.

## Tự kiểm trước khi bàn giao

- [ ] Đã đọc toàn bộ diff trước khi đọc `04`, `05`.
- [ ] Mọi mục trong danh sách có kết quả, kể cả "không có vấn đề".
- [ ] Đã đối chiếu kết quả test với log.
- [ ] Mỗi phát hiện có mức, vị trí và đề xuất.
