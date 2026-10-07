# .agents — quy trình làm việc với AI agent

Bộ quy trình dùng chung cho Claude Code, Codex và Antigravity. Repo này được gắn vào project dưới dạng submodule tại `.agents/` ở gốc superproject.

## Cấu trúc

| Đường dẫn | Vai trò |
|---|---|
| `core.md` | Rule always-on. `scripts/sync.py` chép vào khối CORE của `AGENTS.md`. |
| `skills/<tên>/SKILL.md` | Skill theo chuẩn Agent Skills, dùng chung cho cả ba tool. Mọi skill có tiền tố `wf-`. |
| `templates/` | Mẫu artifact từng giai đoạn, mẫu `AGENTS.md` cho project mới, mẫu CI. |
| `scripts/gate.py` | Cổng duyệt: trạng thái, kiểm tra, `approve` (chỉ người), `reopen`, `validate`. |
| `scripts/scope.py` | So file thực sự thay đổi với phạm vi được phép của giai đoạn. |
| `scripts/guard.py` | Hook PreToolUse của Claude Code: chặn tự duyệt, sửa artifact đã duyệt, lệnh git nguy hiểm. |
| `scripts/sync.py` | Đồng bộ `core.md` vào `AGENTS.md`. |
| `scripts/testcase_xlsx.py` | Dựng bộ test case Excel từ spec JSON và gộp vào file tổng (skill `wf-testcase`). Cần `openpyxl`. |
| `scripts/doctor.py` | Kiểm tra và sửa môi trường, đăng ký hook, cài git hook. |
| `scripts/tests/` | Unit test của các script (pytest). |
| `evals/` | Eval kích hoạt skill và hành vi. |

## Mỗi tool đọc gì

| Tool | Rule always-on | Skill |
|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills` |
| Antigravity | `AGENTS.md` | `.agents/skills` |
| Claude Code | `CLAUDE.md` → `@AGENTS.md` | `.claude/skills` (symlink hoặc bản copy do `doctor.py` tạo) |

Luôn mở agent ở **gốc superproject**. Mở riêng một submodule thì agent không thấy `AGENTS.md` gốc lẫn `.agents/`.

### Claude Code load quy trình thế nào

```
<superproject>/
├── .agents/skills/<tên>/SKILL.md          ← nguồn duy nhất
├── .claude/skills → ../.agents/skills     ← doctor tạo trên từng máy, gitignore
├── .claude/settings.local.json            ← doctor đăng ký hook, theo Python của máy, gitignore
├── AGENTS.md                              ← sync.py điền khối CORE
└── CLAUDE.md                              ← đúng một dòng: @AGENTS.md
```

1. Claude **không** đọc `.agents/skills`. Chưa chạy `doctor.py --fix` thì Claude không thấy skill nào.
2. `CLAUDE.md` import `AGENTS.md`, nên rule luôn nằm trong context.
3. Claude quét `.claude/skills` (đi theo symlink); lúc khởi động chỉ nạp `name` và `description`, nạp toàn bộ `SKILL.md` khi skill được gọi.
4. Windows không tạo được symlink (chưa bật Developer Mode) thì doctor dùng bản copy. Hook `SessionStart` tự làm mới bản copy khi `.agents` đổi; skill mới có hiệu lực từ phiên sau. Nên bật Developer Mode để dùng symlink.
5. Không bật chế độ đọc cả `CLAUDE.md` lẫn `AGENTS.md` trong `/config` của Claude Code cho repo này; `AGENTS.md` sẽ bị nạp hai lần.

## Cài đặt cho project mới (làm một lần)

1. `git submodule add <url-repo-.agents> .agents`
2. Copy `.agents/templates/AGENTS.project.md` ra gốc thành `AGENTS.md`, viết phần "Dự án", đặc biệt mục "Vai trò submodule" (`scope.py` đọc mục này).
3. Tạo `CLAUDE.md` ở gốc với đúng một dòng: `@AGENTS.md`
4. Copy `.agents/templates/ci/agents-check.yml` vào `.github/workflows/`. **Bắt buộc**: đây là lớp chặn cuối cho approval bị sửa tay.
5. `python .agents/scripts/doctor.py --fix`, rồi commit `AGENTS.md`, `CLAUDE.md`, `.gitignore`, `.github/workflows/agents-check.yml`.

## Cho thành viên sau khi clone

```
git clone --recursive <url-superproject>      # hoặc: git submodule update --init --recursive
python .agents/scripts/doctor.py --fix
```

Trên Windows lệnh Python có thể là `py`. `--fix` làm: sync CORE, tạo `.claude/skills`, đăng ký hook Claude, cài git hook `pre-commit` (sync --check, gate validate) và `post-merge`/`post-checkout`, thêm dòng `.gitignore`.

Kiểm tra cuối: mở từng tool ở gốc repo, hỏi "liệt kê các skill bạn đang thấy". Phải có `wf-requirement`.

## Dùng hằng ngày

Cả ba tool dùng chung tên lệnh: Claude và Antigravity gõ `/wf-…`, Codex gõ `$wf-…`.

| Giai đoạn | Lệnh | Artifact |
|---|---|---|
| Không nhớ đang ở đâu | `/wf-status` | |
| Làm bước kế tiếp | `/wf-next <task-id>` | |
| 1. Phân tích tính năng | `/wf-requirement` | `01-requirement.md` |
| 1. Điều tra bug | `/wf-bug` | `01-requirement.md` |
| 2. Contract (khi `contract_change: yes`) | `/wf-contract` | `02-contract.md` |
| 3. Plan | `/wf-plan` | `03-plan.md` |
| 4. Implement | `/wf-implement` | `04-impl-notes.md` |
| 5. Test tích hợp | `/wf-test` | `05-test-report.md` |
| 6. Review | `/wf-review` | `06-review.md` |
| Tạm dừng, chuyển máy hay tool | `/wf-handoff` | |

Task **size S** (không chạm vùng rủi ro, không đổi contract, khoảng 3 file / 50 dòng) chỉ có 1 → 4 → 6; `01` chứa luôn bảng file và checklist.

Skill chuyên đề không cần gọi; agent tự dùng khi task chạm vùng tương ứng: `wf-git`, `wf-db-migration`, `wf-health-endpoint`, `wf-testcase`.

`wf-testcase` chạy ở cuối giai đoạn test (task S: cuối implement): agent viết `work/<task-id>/testcases.json`, `scripts/testcase_xlsx.py` dựng `testcases.xlsx` theo mẫu test case của team (9 cột, khối tổng, bảng EP, bảng quyết định, sheet Report có Bug Report) và gộp vào file tổng khai báo ở vai trò `testcase-book` trong `AGENTS.md`. Cần `openpyxl` (`python -m pip install openpyxl`).

Mỗi giai đoạn kết thúc bằng một artifact `draft` và agent dừng lại. Nên chạy `wf-review` trong phiên mới, tốt nhất trên tool khác với tool đã implement.

### Duyệt

Đọc artifact, rồi **tự chạy trong terminal của bạn** (không qua agent):

```
python .agents/scripts/gate.py approve <task-id> <giai-đoạn>
```

Lệnh hỏi lại task ID để xác nhận, rồi ghi `approved_by` (từ `git config user.name`), `approved_at`, `content_hash` của artifact và `inputs` (hash các artifact đầu vào). Không sửa tay các trường này; `gate.py` coi approval thiếu hash là không hợp lệ.

- Sửa một artifact sau khi duyệt → approval đó hết hiệu lực.
- Sửa và duyệt lại một artifact đầu vào → mọi artifact phía sau dựa trên bản cũ bị đánh dấu "ĐÃ CŨ" và phải duyệt lại.
- Quay lại giai đoạn trước: `python .agents/scripts/gate.py reopen <task-id> <giai-đoạn>`.
- Xem trạng thái: `python .agents/scripts/gate.py <task-id>` (bỏ trống task ID thì suy từ tên nhánh).

### Các lớp chặn và giới hạn

| Rào chắn | Claude Code | Codex, Antigravity |
|---|---|---|
| Agent không tự duyệt | Hook `guard.py` chặn ghi trường duyệt và chặn `gate.py approve`; `approve` từ chối khi không có terminal hoặc có biến môi trường của agent | `approve` từ chối khi không có terminal; prompt; CI `gate.py validate` |
| Không sửa artifact đã duyệt | Hook chặn; hash phát hiện | Hash phát hiện (`gate.py`, pre-commit, CI) |
| Chỉ sửa file trong plan | `scope.py` trong skill implement, review | như Claude |
| Lệnh git nguy hiểm | Hook chặn | Prompt; dùng chế độ approval của tool cho lệnh shell |

Không lớp nào tuyệt đối: một agent có terminal tương tác vẫn có thể gõ xác nhận. Lớp cuối là người review PR theo Definition of Done. CI không so author của commit với `approved_by`, vì agent commit bằng chính danh tính git của người dùng nên phép so đó không chứng minh được gì.

## Sửa quy trình

- Sửa rule chung: sửa `core.md`, rồi trong từng project chạy `python .agents/scripts/sync.py` và commit `AGENTS.md`.
- Thêm skill: `skills/wf-<tên>/SKILL.md`, `name` trùng tên thư mục, frontmatter chỉ có `name` và `description` (doctor kiểm tra; trường khác chưa được xác nhận an toàn trên cả ba tool). Description ghi rõ **trạng thái** khi nào dùng skill, không chứa `": "`. Ngay dưới tiêu đề là mục `## Vai trò` gồm vai trò (một cụm từ), chịu trách nhiệm, ưu tiên khi mâu thuẫn, mặc định, không làm.
- Trong `.agents/` không nhắc tên tool cụ thể trong nội dung skill, và không hardcode tên riêng của dự án; thông tin dự án đọc từ phần "Dự án" của `AGENTS.md`. Ngoại lệ hiện tại: `wf-db-migration` (Supabase) và `wf-health-endpoint` (DrugTime), sẽ tách sang lớp skill riêng của dự án khi có project thứ hai.
- Không đặt file `AGENTS.md`, `GEMINI.md` hay thư mục `rules/` trong `.agents/`: Antigravity sẽ nạp chúng như rule. Doctor kiểm tra.
- Sau khi sửa: `python -m pytest .agents/scripts/tests -q`, chạy eval trong `evals/`, commit và push repo `.agents`, rồi bump con trỏ submodule ở superproject.
- Mỗi sprint: gom mục "Ghi chú cho quy trình" trong các `06-review.md`, sửa skill và thêm ca eval tương ứng.
