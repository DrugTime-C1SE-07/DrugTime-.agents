#!/usr/bin/env python3
"""Cổng duyệt giữa các giai đoạn. Chạy từ bất kỳ đâu trong superproject.

    python .agents/scripts/gate.py [<task>]                 # trạng thái task (bỏ trống: suy từ tên nhánh)
    python .agents/scripts/gate.py [<task>] <stage>         # có được bắt đầu <stage> không
    python .agents/scripts/gate.py current                  # in task ID suy từ tên nhánh
    python .agents/scripts/gate.py approve <task> <stage> [--by <tên>]   # CHỈ NGƯỜI DUYỆT, trong terminal
    python .agents/scripts/gate.py reopen <task> <stage>    # đặt artifact về draft để sửa
    python .agents/scripts/gate.py validate [--strict]      # kiểm mọi artifact trong work/ (CI, pre-commit)

<task>: `1.10-auth`, `work/1.10-auth` hoặc đường dẫn. Luôn tính từ gốc superproject.
stage: requirement | contract | plan | implement | test | review
Exit code: 0 = được phép / hợp lệ, 1 = bị chặn / có lỗi, 2 = dùng sai.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    APPROVAL_KEYS, ARTIFACT, ROOT, STAGE_NAMES, WORK, content_hash, git_user, infer_task_ids,
    parse_frontmatter, read_text, resolve_task_dir, set_frontmatter_fields,
)

AGENT_ENV_VARS = ("CLAUDECODE", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED")


# ---------------------------------------------------------------- đọc trạng thái

def fm_of(task_dir: Path, stage: str) -> dict | None:
    path = task_dir / ARTIFACT[stage]
    if not path.exists():
        return None
    return parse_frontmatter(read_text(path))[0]


def requirement_problems(task_dir: Path) -> list[str]:
    """Các trường của 01 quyết định luồng; phải rõ ràng trước khi rời giai đoạn requirement."""
    fm = fm_of(task_dir, "requirement")
    if fm is None:
        return [f"Thiếu {ARTIFACT['requirement']}."]
    out = []
    cc = fm.get("contract_change", "").lower()
    size = fm.get("size", "").upper()
    if cc not in ("yes", "no"):
        out.append(f"contract_change đang là '{cc or 'trống'}', phải là yes hoặc no.")
    if size not in ("S", "M", "L"):
        out.append(f"size đang là '{size or 'trống'}', phải là S, M hoặc L.")
    if size == "S" and cc == "yes":
        out.append("Task size S không được đổi contract. Xếp lại size M.")
    return out


def flow(task_dir: Path) -> list[str]:
    """Các giai đoạn áp dụng cho task, theo size và contract_change trong 01."""
    fm = fm_of(task_dir, "requirement") or {}
    if fm.get("size", "").upper() == "S":
        return ["requirement", "implement", "review"]
    stages = ["requirement"]
    if fm.get("contract_change", "").lower() == "yes":
        stages.append("contract")
    return stages + ["plan", "implement", "test", "review"]


def inputs_of(task_dir: Path, stage: str) -> list[str]:
    f = flow(task_dir)
    return f[: f.index(stage)] if stage in f else []


def approval_problems(task_dir: Path, stage: str) -> list[str]:
    """Rỗng nếu artifact đang approved và còn hiệu lực. Ngược lại liệt kê lý do."""
    path = task_dir / ARTIFACT[stage]
    if not path.exists():
        return [f"Thiếu {ARTIFACT[stage]}."]
    text = read_text(path)
    fm, errors = parse_frontmatter(text)
    if errors:
        return [f"{ARTIFACT[stage]}: frontmatter lỗi ({'; '.join(errors)})."]
    st = fm.get("status", "").lower() or "thiếu status"
    if st != "approved":
        return [f"{ARTIFACT[stage]} đang ở trạng thái '{st}', chưa được người duyệt."]
    missing = [k for k in ("approved_by", "approved_at", "content_hash") if not fm.get(k)]
    if missing:
        return [f"{ARTIFACT[stage]} ghi approved nhưng thiếu {', '.join(missing)}. "
                "Approval hợp lệ chỉ được tạo bằng `gate.py approve` do người duyệt chạy."]
    probs = []
    if fm["content_hash"] != content_hash(text):
        probs.append(f"{ARTIFACT[stage]} đã bị sửa sau khi duyệt. Cần duyệt lại.")
    recorded = fm.get("inputs") if isinstance(fm.get("inputs"), dict) else {}
    for prev in inputs_of(task_dir, stage):
        pf = ARTIFACT[prev]
        ppath = task_dir / pf
        if pf not in recorded:
            probs.append(f"{ARTIFACT[stage]} được duyệt khi chưa có {pf}. Cần duyệt lại.")
        elif ppath.exists() and recorded[pf] != content_hash(read_text(ppath)):
            probs.append(f"{pf} đã thay đổi sau khi {ARTIFACT[stage]} được duyệt. Cần duyệt lại {ARTIFACT[stage]}.")
    return probs


def label_of(task_dir: Path, stage: str) -> str:
    if stage not in flow(task_dir):
        return "bỏ qua"
    fm = fm_of(task_dir, stage)
    if fm is None:
        return "chưa có"
    st = fm.get("status", "").lower() or "thiếu status"
    if st != "approved":
        return st
    probs = approval_problems(task_dir, stage)
    return "approved" if not probs else "approved nhưng ĐÃ CŨ: " + " ".join(probs)


def next_stage(task_dir: Path) -> str | None:
    for stage in flow(task_dir):
        if approval_problems(task_dir, stage):
            return stage
    return None


# ---------------------------------------------------------------- kiểm cổng

def check(task_dir: Path, stage: str, current_user: str | None = None) -> list[str]:
    problems: list[str] = []
    if stage != "requirement":
        if not task_dir.is_dir():
            return [f"Chưa có thư mục {task_dir}. Hãy bắt đầu từ giai đoạn requirement."]
        problems += requirement_problems(task_dir)
        if problems:
            return problems
        if stage not in flow(task_dir):
            fm = fm_of(task_dir, "requirement") or {}
            why = "size S" if fm.get("size", "").upper() == "S" else "contract_change: no"
            return [f"Task này không có giai đoạn '{stage}' ({why}). Giai đoạn kế tiếp: {next_stage(task_dir)}."]
    for prev in inputs_of(task_dir, stage):
        problems += approval_problems(task_dir, prev)
    own = fm_of(task_dir, stage)
    if own is not None and own.get("status", "").lower() == "approved":
        problems.append(f"{ARTIFACT[stage]} đã approved. Muốn sửa, người dùng chạy "
                        f"`gate.py reopen {task_dir.name} {stage}` trước.")
    if stage == "implement" and own is not None:
        owner = own.get("owner", "")
        me = current_user if current_user is not None else git_user()
        if owner and me and owner != me:
            problems.append(f"{ARTIFACT[stage]} đang do '{owner}' làm (bạn là '{me}'). "
                            "Nếu đã bàn giao, người dùng sửa trường owner rồi chạy lại.")
    return problems


# ---------------------------------------------------------------- duyệt

def do_approve(task_dir: Path, stage: str, by: str, now: str) -> str:
    """Ghi approval vào artifact. Trả về nội dung mới. Ném ValueError nếu không được duyệt."""
    path = task_dir / ARTIFACT[stage]
    if not path.exists():
        raise ValueError(f"Chưa có {path}.")
    if stage not in flow(task_dir):
        raise ValueError(f"Task này không có giai đoạn '{stage}'.")
    if not by:
        raise ValueError("Không xác định được người duyệt. Dùng --by <tên> hoặc đặt git config user.name.")
    if stage == "requirement":
        probs = requirement_problems(task_dir)
    else:
        probs = [p for prev in inputs_of(task_dir, stage) for p in approval_problems(task_dir, prev)]
    if probs:
        raise ValueError("Chưa duyệt được:\n  - " + "\n  - ".join(probs))
    text = read_text(path)
    fm, errors = parse_frontmatter(text)
    if errors:
        raise ValueError("Frontmatter lỗi: " + "; ".join(errors))
    if fm.get("status", "").lower() == "approved":
        raise ValueError(f"{ARTIFACT[stage]} đã approved rồi.")
    inputs = {ARTIFACT[p]: content_hash(read_text(task_dir / ARTIFACT[p])) for p in inputs_of(task_dir, stage)}
    fields: dict = {"status": "approved", "approved_by": by, "approved_at": now,
                    "content_hash": content_hash(text)}
    if inputs:
        fields["inputs"] = inputs
    new = set_frontmatter_fields(text, fields, drop=APPROVAL_KEYS)
    path.write_text(new, encoding="utf-8", newline="\n")
    return new


def do_reopen(task_dir: Path, stage: str) -> None:
    path = task_dir / ARTIFACT[stage]
    if not path.exists():
        raise ValueError(f"Chưa có {path}.")
    new = set_frontmatter_fields(read_text(path), {"status": "draft"}, drop=APPROVAL_KEYS)
    path.write_text(new, encoding="utf-8", newline="\n")


def cmd_approve(args: list[str]) -> int:
    by = None
    if "--by" in args:
        i = args.index("--by")
        by = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
    if len(args) != 2 or args[1] not in STAGE_NAMES:
        print(__doc__)
        return 2
    task_dir, stage = resolve_task_dir(args[0]), args[1]
    agent_vars = [v for v in AGENT_ENV_VARS if os.environ.get(v)]
    if agent_vars or not sys.stdin.isatty():
        print("TỪ CHỐI: `approve` chỉ dành cho người duyệt, chạy trong terminal của chính bạn "
              "(không qua agent). " + (f"Phát hiện môi trường agent: {', '.join(agent_vars)}." if agent_vars else
                                       "stdin không phải terminal."))
        return 1
    print(f"Duyệt {task_dir / ARTIFACT[stage]}")
    for prev in inputs_of(task_dir, stage):
        print(f"  dựa trên {ARTIFACT[prev]}")
    print("Bạn đã tự đọc artifact này chưa? Gõ lại task ID để xác nhận: ", end="", flush=True)
    if input().strip() != task_dir.name:
        print("Không khớp. Hủy.")
        return 1
    try:
        do_approve(task_dir, stage, by if by is not None else git_user(),
                   datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z"))
    except ValueError as e:
        print(f"CHẶN: {e}")
        return 1
    print(f"OK: đã duyệt {ARTIFACT[stage]}. Nhớ commit thư mục {WORK}/{task_dir.name}/.")
    return 0


# ---------------------------------------------------------------- validate (CI)

def validate(root: Path, strict: bool = False) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    work = root / WORK
    if not work.is_dir():
        return errors, warns
    for task_dir in sorted(p for p in work.iterdir() if p.is_dir()):
        for stage in STAGE_NAMES:
            path = task_dir / ARTIFACT[stage]
            if not path.exists():
                continue
            rel = path.relative_to(root).as_posix()
            text = read_text(path)
            fm, perrs = parse_frontmatter(text)
            if perrs or not fm:
                errors.append(f"{rel}: frontmatter lỗi hoặc thiếu ({'; '.join(perrs) or 'không có'}).")
                continue
            st = fm.get("status", "").lower()
            if st not in ("draft", "approved"):
                errors.append(f"{rel}: status '{st}' không hợp lệ.")
                continue
            if st != "approved":
                continue
            missing = [k for k in ("approved_by", "approved_at", "content_hash") if not fm.get(k)]
            if missing:
                errors.append(f"{rel}: approved nhưng thiếu {', '.join(missing)} (không do gate.py approve tạo).")
            elif fm["content_hash"] != content_hash(text):
                errors.append(f"{rel}: bị sửa sau khi duyệt.")
            else:
                stale = [p for p in approval_problems(task_dir, stage) if "sau khi" in p or "khi chưa có" in p]
                (errors if strict else warns).extend(f"{rel}: {p}" for p in stale)
    return errors, warns


# ---------------------------------------------------------------- CLI

def print_status(task_dir: Path) -> None:
    if not task_dir.is_dir():
        print(f"Chưa có thư mục {task_dir}.")
        return
    fm = fm_of(task_dir, "requirement") or {}
    print(f"Task: {task_dir.name}  (size: {fm.get('size') or '?'}, contract_change: {fm.get('contract_change') or '?'})")
    for stage in STAGE_NAMES:
        print(f"  {ARTIFACT[stage]:<22} {label_of(task_dir, stage)}")
    nxt = next_stage(task_dir)
    print(f"Giai đoạn cần làm hoặc chờ duyệt: {nxt or 'không còn (đã xong)'}")


def main(argv: list[str]) -> int:
    args = argv[1:]
    try:
        if args[:1] == ["approve"]:
            return cmd_approve(args[1:])
        if args[:1] == ["reopen"]:
            if len(args) != 3 or args[2] not in STAGE_NAMES:
                print(__doc__)
                return 2
            do_reopen(resolve_task_dir(args[1]), args[2])
            print(f"OK: {ARTIFACT[args[2]]} đã về draft. Các giai đoạn sau sẽ bị chặn tới khi duyệt lại.")
            return 0
        if args[:1] == ["validate"]:
            errors, warns = validate(ROOT, strict="--strict" in args)
            for w in warns:
                print(f"  [WARN] {w}")
            for e in errors:
                print(f"  [LỖI]  {e}")
            print(f"validate: {len(errors)} lỗi, {len(warns)} cảnh báo.")
            return 1 if errors else 0
        if args[:1] == ["current"]:
            ids = infer_task_ids()
            print("\n".join(ids) if ids else "(không suy ra được task từ tên nhánh)")
            return 0 if len(ids) == 1 else 1
        if len(args) > 2 or any(a.startswith("-") for a in args):
            print(__doc__)
            return 2
        task_arg, stage = None, None
        if len(args) == 2:
            task_arg, stage = args
        elif len(args) == 1:
            if args[0].lower() in STAGE_NAMES and not (ROOT / WORK / args[0]).exists():
                stage = args[0]
            else:
                task_arg = args[0]
        task_dir = resolve_task_dir(task_arg)
    except (LookupError, ValueError) as e:
        print(f"LỖI: {e}")
        return 1 if isinstance(e, ValueError) else 2
    if stage is None:
        print_status(task_dir)
        return 0
    stage = stage.lower()
    if stage not in STAGE_NAMES:
        print(f"Stage không hợp lệ: {stage}. Chọn một trong: {', '.join(STAGE_NAMES)}")
        return 2
    problems = check(task_dir, stage)
    if problems:
        print(f"CHẶN: chưa được bắt đầu giai đoạn '{stage}' của {task_dir.name}.")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: được bắt đầu giai đoạn '{stage}' của {task_dir.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
