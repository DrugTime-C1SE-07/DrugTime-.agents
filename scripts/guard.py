#!/usr/bin/env python3
"""Hook PreToolUse cho Claude Code: chặn agent làm những việc mà quy trình dành cho người.

Đọc JSON của hook từ stdin. Exit 2 (kèm lý do ở stderr) để chặn; exit 0 để cho qua.
Được `doctor.py --fix` đăng ký trong .claude/settings.local.json với matcher
"Edit|Write|MultiEdit|Bash|PowerShell".

Chặn:
  - Sửa artifact work/<task>/0x-*.md đang approved (người dùng phải `gate.py reopen` trước).
  - Ghi các trường duyệt (status: approved, approved_by, approved_at, content_hash, inputs) vào artifact.
  - Sửa bản copy trong .claude/skills (sửa ở .agents/skills).
  - Lệnh: gate.py approve, git push --force, reset --hard, clean -f, xóa nhánh,
    submodule update --remote. Người dùng tự chạy các lệnh này nếu thực sự muốn.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import ROOT, WORK, parse_frontmatter, read_text  # noqa: E402

ARTIFACT_RE = re.compile(r"^0[1-6]-[\w-]+\.md$")
APPROVAL_RE = re.compile(
    r"^[ \t]*(status[ \t]*:[ \t]*['\"]?approved\b|approved_by[ \t]*:[ \t]*\S|approved_at[ \t]*:[ \t]*\S"
    r"|content_hash[ \t]*:|inputs[ \t]*:)",
    re.I | re.M,
)
SEG = r"[^\n;&|]*"
BASH_RULES = [
    (rf"\bgate\.py\b{SEG}\bapprove\b", "Chỉ người duyệt chạy `gate.py approve`, trong terminal của họ."),
    (rf"\bgit\b{SEG}\bpush\b{SEG}(--force\b|--force-with-lease\b|\s-[a-zA-Z]*f\b|\s\+[\w/.-]+)",
     "Không push --force khi chưa được yêu cầu rõ. Người dùng tự chạy nếu cần."),
    (rf"\bgit\b{SEG}\bpush\b{SEG}(--delete\b|\s:[\w/.-]+)", "Không xóa nhánh trên remote."),
    (rf"\bgit\b{SEG}\breset\b{SEG}--hard\b", "Không reset --hard; có thể mất thay đổi của người khác."),
    (rf"\bgit\b{SEG}\bclean\b{SEG}\s-[a-zA-Z]*f", "Không git clean -f; có thể xóa file chưa track của người khác."),
    (rf"\bgit\b{SEG}\bbranch\b{SEG}\s(-D|-d|--delete)\b", "Không xóa nhánh khi chưa được yêu cầu rõ."),
    (rf"\bgit\b{SEG}\bsubmodule\b{SEG}\bupdate\b{SEG}--remote\b",
     "Không `submodule update --remote` hàng loạt; nó dời mọi con trỏ submodule."),
]


def block(reason: str) -> int:
    print(f"[agents guard] {reason}", file=sys.stderr)
    return 2


def _resolve(path_str: str, cwd: str | None) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(cwd or ROOT) / p
    return p.resolve()


def check_edit(tool_input: dict, cwd: str | None) -> str | None:
    path_str = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path_str:
        return None
    p = _resolve(path_str, cwd)
    try:
        rel = p.relative_to(ROOT)
    except ValueError:
        return None
    parts = rel.parts
    if parts[:2] == (".claude", "skills"):
        return "`.claude/skills` là bản sinh ra từ `.agents/skills`. Sửa skill trong `.agents/skills`."
    if len(parts) == 3 and parts[0] == WORK and ARTIFACT_RE.match(parts[2]):
        if p.exists():
            fm, _ = parse_frontmatter(read_text(p))
            if fm.get("status", "").lower() == "approved":
                return (f"{rel.as_posix()} đã approved nên không được sửa. Nêu thay đổi đề xuất; người dùng "
                        f"chạy `python .agents/scripts/gate.py reopen {parts[1]} <stage>` nếu đồng ý.")
        texts = [tool_input.get("content", ""), tool_input.get("new_string", "")]
        texts += [e.get("new_string", "") for e in tool_input.get("edits", []) or []]
        if any(APPROVAL_RE.search(t or "") for t in texts):
            return ("Agent không được ghi status: approved, approved_by, approved_at, content_hash hay inputs. "
                    "Người duyệt chạy `python .agents/scripts/gate.py approve <task> <stage>` trong terminal.")
    return None


def check_command(cmd: str) -> str | None:
    for pattern, reason in BASH_RULES:
        if re.search(pattern, cmd):
            return reason
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        print("[agents guard] không đọc được JSON của hook; bỏ qua.", file=sys.stderr)
        return 0
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool in ("Bash", "PowerShell"):
        reason = check_command(tool_input.get("command", ""))
    elif tool in ("Edit", "Write", "MultiEdit"):
        reason = check_edit(tool_input, data.get("cwd"))
    else:
        reason = None
    return block(reason) if reason else 0


if __name__ == "__main__":
    sys.exit(main())
