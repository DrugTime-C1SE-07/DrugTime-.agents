#!/usr/bin/env python3
"""Đối chiếu file thực sự thay đổi với phạm vi được phép của giai đoạn.

    python .agents/scripts/scope.py [<task>] [--stage <stage>]

stage (mặc định implement):
  requirement, plan, review  -> không được sửa gì ngoài work/<task>/
  contract                   -> chỉ submodule có vai trò `contract` trong AGENTS.md
  implement                  -> chỉ file trong bảng "File sẽ thay đổi" của plan (task S: của 01),
                                trừ vùng `integration-test`
  test                       -> chỉ vùng `integration-test` trong AGENTS.md
File tổng test case (vai trò `testcase-book`) được phép ở implement và test (skill wf-testcase).

File "thay đổi" gồm thay đổi chưa commit ở mọi submodule, cộng các commit trên nhánh task
(nhánh `<loại>/<task-id>`) so với nhánh gốc ghi trong .gitmodules.
Đường dẫn trong plan có thể là glob, ví dụ `src/drugtime/modules/auth/**`.
Exit code: 0 = trong phạm vi, 1 = có file ngoài phạm vi, 2 = dùng sai.
"""
from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    ROOT, STAGE_NAMES, WORK, base_branch, git, project_roles, read_frontmatter, read_text,
    resolve_task_dir, submodules, task_id_from_branch,
)

HEADING = re.compile(r"^#+\s.*file sẽ thay đổi", re.I)


def plan_entries(task_dir: Path) -> list[str]:
    """Đường dẫn (tính từ gốc superproject) trong bảng "File sẽ thay đổi"."""
    req = task_dir / "01-requirement.md"
    small = req.exists() and read_frontmatter(req).get("size", "").upper() == "S"
    path = req if small else task_dir / "03-plan.md"
    if not path.exists():
        raise LookupError(f"Không có {path.name} để đọc phạm vi.")
    lines = read_text(path).split("\n")
    start = next((i for i, l in enumerate(lines) if HEADING.match(l)), None)
    if start is None:
        raise LookupError(f"{path.name} không có mục 'File sẽ thay đổi'.")
    rows = []
    for l in lines[start + 1:]:
        if l.startswith("#"):
            break
        if l.strip().startswith("|"):
            rows.append([c.strip() for c in l.strip().strip("|").split("|")])
    if len(rows) < 2:
        return []
    header = [h.lower() for h in rows[0]]
    try:
        i_sm = next(i for i, h in enumerate(header) if "submodule" in h)
        i_path = next(i for i, h in enumerate(header) if "đường dẫn" in h or "path" in h)
    except StopIteration:
        raise LookupError(f"Bảng 'File sẽ thay đổi' trong {path.name} cần cột Submodule và Đường dẫn.")
    out = []
    for row in rows[2:]:
        if len(row) <= max(i_sm, i_path):
            continue
        sm = row[i_sm].strip("` ").strip("/")
        for p in re.split(r"<br\s*/?>|,", row[i_path]):
            p = p.strip().strip("`").strip().lstrip("./")
            if not p:
                continue
            if sm and sm not in (".", "superproject", "(gốc)") and not p.startswith(sm + "/"):
                p = f"{sm}/{p}"
            out.append(p)
    return out


def _porcelain(cwd: Path) -> list[str]:
    res = git("status", "--porcelain", "-z", "-uall", cwd=cwd)
    parts = res.stdout.split("\0")
    files, i = [], 0
    while i < len(parts):
        entry = parts[i]
        if len(entry) > 3:
            files.append(entry[3:])
            if entry[0] in "RC":
                i += 1  # bỏ đường dẫn gốc của rename
        i += 1
    return files


def changed_files(task_id: str, root: Path) -> list[str]:
    sm_paths = [sm["path"] for sm in submodules(root)]
    changed: set[str] = set()
    for sm in sm_paths:
        p = root / sm
        if not (p / ".git").exists():
            continue
        changed |= {f"{sm}/{f}" for f in _porcelain(p)}
        br = git("branch", "--show-current", cwd=p).stdout.strip()
        if br and task_id_from_branch(br) == task_id:
            base = base_branch(sm, root)
            ref = f"origin/{base}" if git("rev-parse", "--verify", "-q", f"origin/{base}", cwd=p).returncode == 0 else base
            diff = git("diff", "--name-only", "-z", f"{ref}...HEAD", cwd=p).stdout.split("\0")
            changed |= {f"{sm}/{f}" for f in diff if f}
    for f in _porcelain(root):
        f = f.rstrip("/")
        if f not in sm_paths:  # con trỏ submodule không tính là file
            changed.add(f)
    br = git("branch", "--show-current", cwd=root).stdout.strip()
    if br and task_id_from_branch(br) == task_id:
        head = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", cwd=root).stdout.strip()
        ref = head or "main"
        diff = git("diff", "--name-only", "-z", f"{ref}...HEAD", cwd=root).stdout.split("\0")
        changed |= {f for f in diff if f and f not in sm_paths}
    return sorted(changed)


def _match(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if path == pat or path.startswith(pat.rstrip("/") + "/") or fnmatch.fnmatch(path, pat):
            return True
    return False


def evaluate(task_id: str, stage: str, changed: list[str], plan: list[str], roles: dict) -> dict:
    own_work = f"{WORK}/{task_id}/"
    integ = roles.get("integration-test", [])
    contract = roles.get("contract", [])
    book = roles.get("testcase-book", [])
    relevant = [f for f in changed if not f.startswith(own_work)]
    if stage == "implement":
        allowed = lambda f: (_match(f, plan) and not _match(f, integ)) or _match(f, book)  # noqa: E731
    elif stage == "test":
        allowed = lambda f: _match(f, integ) or _match(f, book)  # noqa: E731
    elif stage == "contract":
        allowed = lambda f: _match(f, contract)  # noqa: E731
    else:
        allowed = lambda f: False  # noqa: E731
    outside = [f for f in relevant if not allowed(f)]
    untouched = []
    if stage == "implement":
        untouched = [p for p in plan if "*" not in p and p not in changed and not _match(p, integ)]
    return {"outside": outside, "inside": [f for f in relevant if allowed(f)], "untouched": untouched}


def main(argv: list[str]) -> int:
    args = argv[1:]
    stage = "implement"
    if "--stage" in args:
        i = args.index("--stage")
        stage = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    if stage not in STAGE_NAMES or len(args) > 1:
        print(__doc__)
        return 2
    try:
        task_dir = resolve_task_dir(args[0] if args else None)
        plan = plan_entries(task_dir) if stage == "implement" else []
    except LookupError as e:
        print(f"LỖI: {e}")
        return 2
    roles = project_roles()
    if stage in ("test", "contract") and not roles.get("integration-test" if stage == "test" else "contract"):
        print("LỖI: AGENTS.md chưa khai báo mục 'Vai trò submodule' cho giai đoạn này.")
        return 2
    res = evaluate(task_dir.name, stage, changed_files(task_dir.name, ROOT), plan, roles)
    print(f"Phạm vi giai đoạn '{stage}' của {task_dir.name}:")
    for f in res["inside"]:
        print(f"  [OK]        {f}")
    for f in res["outside"]:
        print(f"  [NGOÀI]     {f}")
    for f in res["untouched"]:
        print(f"  [CHƯA SỬA]  {f}  (có trong plan)")
    if not (res["inside"] or res["outside"]):
        print("  (không có thay đổi nào ngoài work/)")
    if res["outside"]:
        print(f"CHẶN: {len(res['outside'])} file ngoài phạm vi. Ghi vào mục 'Phát sinh' và hỏi người dùng.")
        return 1
    print("OK: mọi thay đổi nằm trong phạm vi.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
