# <Tên project> — hướng dẫn cho AI agent

File này được Codex và Antigravity đọc trực tiếp, Claude Code đọc qua `CLAUDE.md` (`@AGENTS.md`).
Khối giữa hai marker được sinh tự động từ `.agents/core.md`; phần "Dự án" bên dưới do team viết.
Giữ cả file dưới 24 KiB (Codex cắt phần vượt 32 KiB mà không báo); nội dung dài đưa vào skill hoặc tài liệu.

<!-- BEGIN AGENTS-CORE: sinh từ .agents/core.md bằng .agents/scripts/sync.py, KHÔNG sửa tay -->
<!-- END AGENTS-CORE -->

## Dự án

### Cấu trúc repo

<Liệt kê submodule / thư mục chính, mỗi cái làm gì.>

### Vai trò submodule

<!-- scope.py đọc mục này. Giữ đúng định dạng: "- <vai trò>: `đường-dẫn`[, `đường-dẫn`]". Đường dẫn tính từ gốc superproject. -->

- contract: `<submodule chứa hợp đồng API>`
- backend: `<submodule backend>`
- client: `<submodule client>`
- integration-test: `<submodule hoặc thư mục test tích hợp>`
- docs: `<submodule tài liệu>`

### Stack và lệnh

<Ngôn ngữ, framework, kiến trúc lớp, lệnh chạy test, lint, reset DB, chạy local. Định dạng contract và lệnh validate.>

### Git

- Nhánh gốc: theo trường `branch` trong `.gitmodules`.
- Evidence log (`work/<task-id>/evidence/`): <commit | chỉ giữ local>.

### Bất biến kiến trúc

<Những điều không được vi phạm trong mọi task.>

### Vùng rủi ro

<Loại thay đổi nào cần chú ý đặc biệt, và phải kiểm gì khi chạm vào. Task chạm vùng này không được xếp size S.>

### Thang mức nghiêm trọng

<Tùy chọn. Nếu bỏ trống, dùng thang mặc định trong skill wf-bug.>

### Kịch bản chất lượng cho test tích hợp

<Các kịch bản bắt buộc phải có test khi task chạm vùng liên quan.>

### Definition of Done

<Điều kiện để một task được coi là xong.>

### Tài liệu nguồn

<Đường dẫn tới tài liệu yêu cầu, kiến trúc, backlog.>

### Quy ước task ID

<Ví dụ: mã backlog + slug → work/<task-id>/; nhánh `<loại>/<task-id>`.>
