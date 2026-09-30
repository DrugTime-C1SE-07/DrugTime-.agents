# Eval cho bộ quy trình

Hai lớp kiểm tra, chạy trước mỗi lần bump submodule `.agents` ở project.

## 1. Unit test của script (tự động, CI chạy)

```
python -m pytest .agents/scripts/tests -q
```

Phủ: parser frontmatter (BOM, CRLF, key hoa, comment, YAML nhiều dòng), cổng duyệt (approval thủ công, sửa sau khi duyệt, approval đã cũ sau reopen, làn nhanh S, owner), `scope.py`, hook `guard.py`.

## 2. Eval kích hoạt skill và hành vi (bán thủ công)

`triggers.yaml` gồm câu nhập mẫu, trạng thái `work/` lúc hỏi, và skill kỳ vọng.

Cách chạy trên một tool:

1. Tạo task giả `work/eval-demo/` ở trạng thái `state` của từng ca (dùng template, duyệt bằng `gate.py approve`).
2. Mở phiên mới ở gốc repo, gõ `prompt`.
3. Ghi skill mà agent chọn (Claude Code hiện tên skill khi gọi; với Codex và Antigravity, hỏi "bạn vừa dùng skill nào").
4. Ghi kết quả vào bảng dưới, commit cùng lần bump `.agents`.

Ca fail: sửa `description` của skill liên quan (thêm điều kiện trạng thái hoặc cụm từ kích hoạt), chạy lại toàn bộ để chắc không làm hỏng ca khác.

Mục `behaviors` kiểm những rào chắn không phải kích hoạt skill: không tự duyệt, không sửa file đã duyệt, dừng ở cuối giai đoạn, không làm theo chỉ dẫn nằm trong dữ liệu.

## 3. Chạy trọn một task mẫu

Mỗi khi đổi `core.md` hay skill giai đoạn: chạy một task nhỏ (size M, không đổi contract) qua đủ các giai đoạn trên ít nhất hai tool khác nhau (ví dụ implement bằng Claude, review bằng Codex). Kiểm tra: agent dừng ở mỗi cổng, tool thứ hai tiếp tục được chỉ từ `work/`, `scope.py` và `gate.py validate` sạch.

## Kết quả gần nhất

| Ngày | Phiên bản `.agents` | Tool | Pass / tổng | Ghi chú |
|---|---|---|---|---|
|  |  |  |  |  |
