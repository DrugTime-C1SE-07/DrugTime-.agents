#!/usr/bin/env python3
"""Chép .agents/core.md vào khối CORE của AGENTS.md ở gốc superproject.

    python .agents/scripts/sync.py           # cập nhật khối CORE
    python .agents/scripts/sync.py --check   # chỉ kiểm tra, exit 1 nếu lệch (CI, pre-commit)

AGENTS.md phải có sẵn hai dòng marker BEGIN/END (xem .agents/templates/AGENTS.project.md).
Mọi nội dung ngoài hai marker là phần riêng của project và không bị đụng tới.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import AGENTS_DIR, ROOT, read_text  # noqa: E402

CORE = AGENTS_DIR / "core.md"
AGENTS_MD = ROOT / "AGENTS.md"

BEGIN_PREFIX = "<!-- BEGIN AGENTS-CORE"
BEGIN = "<!-- BEGIN AGENTS-CORE: sinh từ .agents/core.md bằng .agents/scripts/sync.py, KHÔNG sửa tay -->"
END = "<!-- END AGENTS-CORE -->"


class SyncError(Exception):
    pass


def render(core_path: Path = CORE, agents_md: Path = AGENTS_MD) -> tuple[str, str]:
    """Trả về (nội dung hiện tại, nội dung sau khi sync) của AGENTS.md."""
    if not core_path.exists():
        raise SyncError(f"Không tìm thấy {core_path}.")
    if not agents_md.exists():
        raise SyncError(
            f"Không tìm thấy {agents_md}. Copy .agents/templates/AGENTS.project.md ra gốc repo "
            "thành AGENTS.md rồi chạy lại."
        )
    current = read_text(agents_md)
    lines = current.split("\n")
    begin_idx = next((i for i, l in enumerate(lines) if l.strip().startswith(BEGIN_PREFIX)), None)
    end_idx = next((i for i, l in enumerate(lines) if l.strip() == END), None)
    if begin_idx is None or end_idx is None or end_idx < begin_idx:
        raise SyncError(
            "AGENTS.md thiếu hoặc sai thứ tự marker. Cần có hai dòng:\n"
            f"  {BEGIN}\n  {END}"
        )
    core = read_text(core_path).strip("\n")
    new_lines = lines[:begin_idx] + [BEGIN, "", core, "", END] + lines[end_idx + 1:]
    return current, "\n".join(new_lines)


def is_in_sync() -> bool:
    current, rendered = render()
    return current == rendered


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    try:
        current, rendered = render()
    except SyncError as e:
        print(f"LỖI: {e}")
        return 1
    if current == rendered:
        print("OK: khối CORE trong AGENTS.md đã khớp .agents/core.md.")
        return 0
    if check_only:
        print("LỆCH: khối CORE trong AGENTS.md khác .agents/core.md. Chạy: python .agents/scripts/sync.py")
        return 1
    AGENTS_MD.write_text(rendered, encoding="utf-8", newline="\n")
    print("Đã cập nhật khối CORE trong AGENTS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
