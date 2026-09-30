---
name: wf-git
description: Quy tắc git cho superproject nhiều submodule — thoát detached HEAD trước khi sửa, đặt tên nhánh theo task, commit trong submodule trước rồi mới bump con trỏ, commit artifact work/ khi xong giai đoạn, mở PR đúng thứ tự merge, xử lý con trỏ sau squash merge và xung đột con trỏ. Use whenever any git operation is needed — before editing files inside a submodule, and when the user asks to "commit", "push", "tạo nhánh", "tạo PR", "merge", "bump submodule", "cập nhật con trỏ", "đẩy code lên", or git shows detached HEAD or a submodule conflict.
---

# Git với submodule

## Vai trò

Người giữ repo.

- **Chịu trách nhiệm**: không commit nào bị mất và con trỏ submodule luôn trỏ tới commit có trên remote.
- **Ưu tiên khi mâu thuẫn**: không mất dữ liệu > lịch sử rõ ràng > tiện lợi.
- **Mặc định**: thay đổi chưa commit có thể là của người khác; thao tác không đảo ngược được cần người dùng yêu cầu rõ.
- **Không làm**: force push, reset, xóa nhánh hay viết lại lịch sử khi chưa được yêu cầu.

Hai lỗi hay gặp nhất: commit trên detached HEAD rồi mất, và bump con trỏ tới commit không có trên remote. Chỉ commit, push, tạo nhánh remote hay mở PR khi người dùng yêu cầu. Nhánh gốc của từng submodule lấy từ trường `branch` trong `.gitmodules`; không có thì hỏi.

## Trước khi sửa file trong một submodule

```
git -C <submodule> status
git -C <submodule> symbolic-ref -q HEAD   # exit khác 0 = detached HEAD
```

- Có thay đổi chưa commit không phải của task này: dừng và hỏi. Không `stash`, `checkout --`, `reset` hay `clean` lên thay đổi của người khác.
- Detached HEAD:
  ```
  git -C <submodule> fetch origin
  git -C <submodule> switch <nhánh-gốc>
  git -C <submodule> pull --ff-only
  git -C <submodule> switch -c <nhánh-task>
  ```
  Nhánh task đã tồn tại (phiên trước hoặc tool khác tạo) thì `switch <nhánh-task>`.
- Con trỏ trong superproject trỏ tới commit khác đầu nhánh gốc: báo người dùng, vì code đang chạy có thể khác nhánh gốc.

## Đặt tên nhánh

`<loại>/<task-id>`, cùng một tên ở superproject và mọi submodule mà task chạm, ví dụ `feat/1.10-auth-register-login`. Loại: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`. `gate.py current` dựa vào tên này để suy ra task ID.

## Commit

- Xem lại trước khi commit: `git -C <submodule> diff --staged`. Chỉ stage file thuộc phạm vi; không `git add -A` khi có file lạ.
- Không commit secret, `.env`, file build, `work/<task-id>/scratch/`.
- Message tiếng Anh theo Conventional Commits, scope là module, footer ghi task:
  ```
  feat(auth): add register endpoint

  Refs: 1.10
  ```

## Artifact `work/`

Khi xong một giai đoạn hoặc tạm dừng, đề xuất với người dùng commit `work/<task-id>/` trên nhánh task của superproject (và push nếu họ đồng ý), để máy khác và tool khác thấy trạng thái. Evidence log commit hay không theo quy định trong `AGENTS.md`.

## Push và bump con trỏ

1. Commit và push từng submodule: `git -C <submodule> push -u origin <nhánh-task>`.
2. Xác nhận commit đã lên remote: `git -C <submodule> branch -r --contains HEAD` phải có kết quả.
3. Ở superproject, trên nhánh cùng tên: `git add <submodule>` rồi commit, ví dụ `chore: bump backend to <sha-ngắn> (1.10)`.
4. Push superproject.

Không bao giờ bump con trỏ tới commit chưa push.

## Pull request và thứ tự merge

- Mỗi submodule bị sửa có một PR, cộng một PR superproject để bump con trỏ. Mô tả mỗi PR liên kết các PR còn lại.
- Thứ tự merge: contract → backend → client → test tích hợp → superproject (tên submodule theo "Vai trò submodule" trong `AGENTS.md`).
- **Sau squash hoặc rebase merge, SHA đổi**: trước khi merge PR superproject, cập nhật con trỏ tới commit đã merge:
  ```
  git -C <submodule> fetch origin
  git -C <submodule> switch <nhánh-gốc>
  git -C <submodule> pull --ff-only
  git add <submodule>
  git commit -m "chore: bump <submodule> to merged <sha-ngắn> (<task-id>)"
  ```

## Xung đột con trỏ submodule

Không chọn bừa "ours" hay "theirs". Xem `git -C <submodule> log --oneline <sha-a> <sha-b> -5`, xác định commit chứa thay đổi của cả hai phía (thường là commit mới hơn trên nhánh gốc), chuyển submodule tới commit đó rồi `git add <submodule>`. Không chắc thì hỏi.

## Không làm nếu người dùng không yêu cầu rõ trong chat

`push --force`, `reset --hard`, `clean -fd`, xóa nhánh, `rebase` nhánh đã push, sửa commit đã push, `submodule update --remote`. Trong Claude Code, hook `guard.py` chặn các lệnh này; nếu người dùng thật sự muốn, họ tự chạy trong terminal.
