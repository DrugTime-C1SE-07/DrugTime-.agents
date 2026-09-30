---
name: wf-db-migration
description: Quy tắc thiết kế, viết và kiểm tra migration Supabase/PostgreSQL — migration mới thay vì sửa migration đã áp dụng, thay đổi an toàn trên bảng có dữ liệu, RLS và grant tối thiểu, bảng log chỉ ghi thêm (revoke và trigger), ràng buộc và index, kiểm bằng reset DB sạch. Use whenever a task adds or changes tables, columns, constraints, indexes, enums, functions, grants or RLS — e.g. "thêm cột", "tạo bảng", "viết migration", "sửa schema", "thêm index", "Supabase migration", "SQL" — during planning, implementation, testing or review.
---

# Migration CSDL

## Vai trò

Người giữ schema.

- **Chịu trách nhiệm**: schema thay đổi an toàn với dữ liệu hiện có, và không quyền nào bị mở rộng ngoài ý muốn.
- **Ưu tiên khi mâu thuẫn**: toàn vẹn dữ liệu > bảo mật > khả năng đảo ngược > tiện cho code.
- **Mặc định**: bảng đã có dữ liệu thật; mọi quyền mặc định là không cấp.
- **Không làm**: sửa migration đã áp dụng, cấp quyền rộng "cho chắc".

Skill dùng bên trong plan, implement, test, review; không có artifact riêng, kết quả ghi vào mục "Migration" của artifact đang làm. Thư mục migration, lệnh reset DB và tên role của API/Worker lấy từ `AGENTS.md`; chưa ghi thì tìm `supabase/migrations` trong các submodule, không thấy thì hỏi.

## Khi lập plan

- Liệt kê mọi thay đổi: bảng, cột, kiểu, ràng buộc, index, enum, grant, RLS.
- Mỗi truy vấn mới chạy thường xuyên (đặc biệt truy vấn phân quyền ở mỗi request): xác định index phục vụ nó.
- Đánh giá thay đổi trên bảng có dữ liệu theo bảng "Thay đổi an toàn".
- Việc cập nhật tài liệu schema hay ERD ghi vào "Phát sinh"; không sửa tài liệu nếu plan không có.

## Viết migration

- Tạo file bằng `supabase migration new <tên_mô_tả>`. Không sửa migration đã merge hoặc đã chạy ở môi trường khác; muốn đổi thì viết migration mới.
- Mỗi migration làm một việc có tên rõ ràng, chạy trọn trong một transaction.
- Thời gian dùng `timestamptz`.
- Ràng buộc đặt ở DB: `NOT NULL`; `FOREIGN KEY` với `ON DELETE` chọn có chủ đích; `UNIQUE` cho khóa idempotency và khóa tự nhiên (cặp khóa dùng cho upsert); `CHECK` cho khoảng giá trị.
- Không ghi dữ liệu thật hay dữ liệu cá nhân vào migration; dữ liệu mẫu để trong seed.

## Thay đổi an toàn trên bảng có dữ liệu

| Thay đổi | Cách làm an toàn |
|---|---|
| Thêm cột `NOT NULL` | Thêm với `DEFAULT`, hoặc nullable → backfill → đặt `NOT NULL` |
| Đổi tên cột hoặc bảng | Phá vỡ code đang chạy; phối hợp với code và contract, nêu trong rủi ro |
| Xóa cột hoặc bảng | Hai bước: code ngừng dùng trước, migration xóa ở task sau |
| Đổi kiểu cột | Kiểm dữ liệu hiện có chuyển đổi được; nêu rủi ro mất dữ liệu |
| Thêm `UNIQUE` hoặc `CHECK` | Kiểm dữ liệu hiện có không vi phạm, hoặc làm sạch trong cùng migration |

## Bảo mật (bắt buộc)

- Bật RLS cho mọi bảng mới: `ALTER TABLE <bảng> ENABLE ROW LEVEL SECURITY;`
- Không tạo policy cho `anon` và `authenticated`; client không đọc DB trực tiếp.
- Grant tối thiểu cho role của API và của Worker: chỉ thao tác mà code thực sự cần trên từng bảng.
- Lưu ý Supabase: `service_role` bỏ qua RLS và mặc định có quyền trên mọi bảng mới. Backend không dùng `service_role` cho truy cập dữ liệu thường ngày; nếu buộc phải dùng, revoke rõ ràng những gì nó không được làm.
- **Bảng log hay audit chỉ ghi thêm** (ví dụ `access_logs`): grant không đủ, vì chủ sở hữu bảng và role có quyền cao vẫn sửa được. Làm cả hai:
  ```sql
  REVOKE UPDATE, DELETE, TRUNCATE ON <bảng_log> FROM PUBLIC, anon, authenticated, service_role, <role_api>, <role_worker>;

  CREATE OR REPLACE FUNCTION forbid_log_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
  BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
  END $$;

  CREATE TRIGGER <bảng_log>_append_only
    BEFORE UPDATE OR DELETE ON <bảng_log>
    FOR EACH ROW EXECUTE FUNCTION forbid_log_mutation();
  CREATE TRIGGER <bảng_log>_no_truncate
    BEFORE TRUNCATE ON <bảng_log>
    FOR EACH STATEMENT EXECUTE FUNCTION forbid_log_mutation();
  ```
- Bảng mới chứa dữ liệu sức khỏe: ghi vào rủi ro để endpoint dùng nó áp dụng `wf-health-endpoint`.

## Kiểm tra

1. Chạy lại toàn bộ migration từ DB sạch (lệnh trong `AGENTS.md`, thường là `supabase db reset`). Phải không lỗi. Lưu log `evidence/<giai-đoạn>-db-reset.log`.
2. RLS và quyền: truy vấn bằng `anon`/`authenticated` vào bảng mới không trả dòng nào; role API và Worker chỉ làm được thao tác đã cấp; `UPDATE`/`DELETE` bảng log bị từ chối kể cả với role có quyền cao.
3. Ràng buộc: chèn dữ liệu vi phạm `UNIQUE` hoặc `CHECK` phải bị từ chối. Với khóa idempotency, việc này nên thành test tích hợp.
4. Chạy unit test của backend.

## Checklist cho review

- [ ] Không migration cũ nào bị sửa.
- [ ] Mọi bảng mới có RLS, không có policy cho `anon`/`authenticated`.
- [ ] Grant tối thiểu; bảng log có revoke và trigger chỉ ghi thêm.
- [ ] Ràng buộc và index đủ cho logic và truy vấn mới.
- [ ] Thay đổi trên bảng có dữ liệu theo cách an toàn.
- [ ] Reset DB sạch chạy thành công trong phiên này, có log.
