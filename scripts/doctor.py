#!/usr/bin/env python3
"""Kiểm tra (và sửa) môi trường để Claude Code, Codex và Antigravity dùng chung bộ .agents.

    python .agents/scripts/doctor.py              # chỉ kiểm tra
    python .agents/scripts/doctor.py --fix        # sửa được gì thì sửa
    python .agents/scripts/doctor.py --fix --copy # dùng bản copy thay cho symlink .claude/skills
    python .agents/scripts/doctor.py --quiet      # chỉ in khi có lỗi hoặc cảnh báo
    python .agents/scripts/doctor.py --session    # cho hook SessionStart: im lặng, tự làm mới bản copy
                                                  # đã cũ, in trạng thái task hiện tại; luôn exit 0
    python .agents/scripts/doctor.py --ci         # cho CI: bỏ các kiểm tra chỉ có nghĩa trên máy cá nhân

--fix làm: sync khối CORE vào AGENTS.md, tạo .claude/skills, đăng ký hook Claude trong
.claude/settings.local.json, cài git hook pre-commit/post-merge/post-checkout, thêm dòng .gitignore.
Exit code: 0 = không có lỗi, 1 = còn lỗi.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib  # noqa: E402
import sync  # noqa: E402
from _lib import AGENTS_DIR, ROOT, git, parse_frontmatter, read_text, submodules  # noqa: E402

SKILLS = AGENTS_DIR / "skills"
CLAUDE_SKILLS = ROOT / ".claude" / "skills"
CLAUDE_LOCAL_SETTINGS = ROOT / ".claude" / "settings.local.json"
COPY_MARKER = ".copied-from-agents"
HOOK_MARKER = "# agents-managed"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_SKILL_KEYS = {"name", "description"}
GITIGNORE_ENTRIES = [".claude/skills", ".claude/settings.local.json", "work/*/scratch/"]
AGENTS_MD_WARN, AGENTS_MD_MAX = 24 * 1024, 32 * 1024  # project_doc_max_bytes mặc định của Codex
FORBIDDEN_IN_AGENTS = ["AGENTS.md", "GEMINI.md", "rules"]  # Antigravity coi đây là rule
# Script chỉ dùng thư viện chuẩn: ghi Python gốc, không ghi Python của venv (venv hay bị xóa, tạo lại).
PY = Path(getattr(sys, "_base_executable", "") or sys.executable).as_posix()
SCRIPTS = (AGENTS_DIR / "scripts").as_posix()


class Report:
    def __init__(self, quiet: bool):
        self.quiet, self.lines, self.errors, self.warnings = quiet, [], 0, 0

    def ok(self, msg):
        self.lines.append(("ok", f"  [OK]   {msg}"))

    def info(self, msg):
        self.lines.append(("info", f"  [INFO] {msg}"))

    def warn(self, msg):
        self.warnings += 1
        self.lines.append(("warn", f"  [WARN] {msg}"))

    def err(self, msg):
        self.errors += 1
        self.lines.append(("err", f"  [LỖI]  {msg}"))

    def flush(self):
        for kind, line in self.lines:
            if not self.quiet or kind in ("warn", "err"):
                print(line)


# ---------------------------------------------------------------- kiểm tra

def check_python(r: Report) -> None:
    if sys.version_info < (3, 10):
        r.err(f"Cần Python >= 3.10, đang dùng {sys.version.split()[0]}.")
    else:
        r.ok(f"Python {sys.version.split()[0]}")


def check_openpyxl(r: Report) -> None:
    """Chỉ testcase_xlsx.py (skill wf-testcase) cần; thiếu thì cảnh báo, không chặn quy trình."""
    import importlib.util
    if importlib.util.find_spec("openpyxl") is None:
        r.warn("Thiếu openpyxl, skill wf-testcase không dựng được file Excel. Cài: python -m pip install openpyxl")
    else:
        r.ok("openpyxl có sẵn (bộ test case Excel)")


def check_root(r: Report) -> None:
    if not (ROOT / ".gitmodules").exists():
        r.warn(f"Không thấy .gitmodules ở {ROOT}. .agents có đang nằm ở gốc superproject không?")
    else:
        r.ok(f"Gốc superproject: {ROOT}")


def check_submodules(r: Report, ci: bool) -> None:
    res = git("submodule", "status")
    if res.returncode != 0:
        r.warn("Không chạy được 'git submodule status'.")
        return
    flags = {}
    for line in res.stdout.splitlines():
        if line:
            rest = line[1:].split(" ", 1)[-1]          # bỏ sha
            path = re.sub(r" \([^)]*\)$", "", rest)      # bỏ "(describe)" ở cuối
            flags[path] = line[0]
    for sm in submodules():
        flag = flags.get(sm["path"], "")
        if flag == "-":
            if not ci:  # CI chỉ lấy .agents
                r.err(f"Submodule {sm['path']} chưa init. Chạy: git submodule update --init --recursive")
        elif flag == "U":
            r.err(f"Submodule {sm['path']} đang xung đột con trỏ. Xem skill wf-git mục 'Xung đột con trỏ'.")
        elif flag == "+":
            r.warn(f"Submodule {sm['path']} đang checkout commit khác con trỏ của superproject.")
    if ci:
        return
    detached = [sm["path"] for sm in submodules()
                if (ROOT / sm["path"]).exists() and git("symbolic-ref", "-q", "HEAD", cwd=ROOT / sm["path"]).returncode != 0]
    if detached:
        r.info("Detached HEAD (bình thường sau khi update; phải vào nhánh trước khi sửa): " + ", ".join(detached))


def check_skills(r: Report) -> list[str]:
    if not SKILLS.is_dir():
        r.err(f"Không có {SKILLS}.")
        return []
    names = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            r.err(f"{d.name}: thiếu SKILL.md")
            continue
        text = read_text(skill_md)
        fm, perrs = parse_frontmatter(text)
        name, desc = fm.get("name", ""), fm.get("description", "")
        extra = set(fm) - ALLOWED_SKILL_KEYS
        raw_desc = next((l.split(":", 1)[1].strip() for l in text.split("\n") if l.startswith("description:")), "")
        if perrs:
            r.err(f"{d.name}: frontmatter lỗi: {'; '.join(perrs)}")
        elif extra:
            r.err(f"{d.name}: trường frontmatter ngoài danh sách cho phép: {', '.join(sorted(extra))}")
        elif name != d.name:
            r.err(f"{d.name}: name trong frontmatter là '{name}', phải trùng tên thư mục")
        elif not NAME_RE.match(name) or len(name) > 64:
            r.err(f"{d.name}: name chỉ gồm a-z, 0-9, dấu '-' và tối đa 64 ký tự")
        elif not desc:
            r.err(f"{d.name}: thiếu description")
        elif len(desc) > 1024:
            r.err(f"{d.name}: description dài {len(desc)} ký tự, tối đa 1024")
        elif not raw_desc.startswith(("'", '"')) and (": " in desc or " #" in desc):
            r.err(f"{d.name}: description chứa ': ' hoặc ' #', làm YAML không hợp lệ. Đổi dấu hoặc bọc trong nháy")
        else:
            names.append(name)
    if names:
        r.ok(f"{len(names)} skill hợp lệ: {', '.join(names)}")
    else:
        r.err(".agents/skills không có skill hợp lệ nào")
    return names


def check_personal_conflicts(r: Report, names: list[str]) -> None:
    home = Path.home()
    for base in (home / ".claude" / "skills", home / ".agents" / "skills", home / ".codex" / "skills"):
        clash = [n for n in names if (base / n).exists()]
        if clash:
            r.warn(f"Skill cá nhân ở {base} trùng tên: {', '.join(clash)}. Lệnh /{clash[0]} có thể gọi nhầm bản.")


def check_forbidden(r: Report) -> None:
    bad = [n for n in FORBIDDEN_IN_AGENTS if (AGENTS_DIR / n).exists()]
    if bad:
        r.err("Trong .agents/ có " + ", ".join(bad) + ": Antigravity sẽ nạp như rule. Đổi tên hoặc chuyển đi.")
    if (AGENTS_DIR / "workflows").exists():
        r.warn(".agents/workflows còn tồn tại; workflow của Antigravity đã ngừng hỗ trợ, dùng skill.")


def check_agents_md(r: Report, fix: bool) -> None:
    try:
        in_sync = sync.is_in_sync()
    except sync.SyncError as e:
        r.err(f"AGENTS.md: {e}")
        return
    if in_sync:
        r.ok("AGENTS.md: khối CORE khớp .agents/core.md")
    elif fix:
        sync.main([])
        r.ok("AGENTS.md: đã sync lại khối CORE")
    else:
        r.err("AGENTS.md: khối CORE lệch .agents/core.md (chạy lại với --fix)")
    size = len((ROOT / "AGENTS.md").read_bytes())
    if size > AGENTS_MD_MAX:
        r.err(f"AGENTS.md {size // 1024} KiB, vượt 32 KiB: Codex sẽ cắt phần cuối mà không báo.")
    elif size > AGENTS_MD_WARN:
        r.warn(f"AGENTS.md {size // 1024} KiB, gần giới hạn 32 KiB của Codex. Chuyển nội dung dài vào skill.")


def check_claude_md(r: Report) -> None:
    path = ROOT / "CLAUDE.md"
    if not path.exists():
        r.err("Thiếu CLAUDE.md ở gốc repo. Nội dung cần có đúng một dòng: @AGENTS.md")
    elif "@AGENTS.md" not in read_text(path):
        r.err("CLAUDE.md không có dòng @AGENTS.md")
    else:
        r.ok("CLAUDE.md import @AGENTS.md")
    parent = ROOT.parent
    stray = [n for n in ("CLAUDE.md", "AGENTS.md", ".agents") if (parent / n).exists()]
    if stray:
        r.warn(f"Thư mục cha {parent} cũng có {', '.join(stray)}: Claude và Codex sẽ nạp thêm bản đó "
               "nếu mở ở cấp cha. Xóa nếu là bản cũ.")


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != COPY_MARKER and "__pycache__" not in p.parts:
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def make_copy() -> None:
    if CLAUDE_SKILLS.is_symlink() or CLAUDE_SKILLS.is_file():
        CLAUDE_SKILLS.unlink()
    elif CLAUDE_SKILLS.exists():
        shutil.rmtree(CLAUDE_SKILLS)
    shutil.copytree(SKILLS, CLAUDE_SKILLS, ignore=shutil.ignore_patterns("__pycache__"))
    (CLAUDE_SKILLS / COPY_MARKER).write_text(
        "Bản copy do .agents/scripts/doctor.py tạo. Không sửa ở đây; sửa trong .agents/skills.\n",
        encoding="utf-8",
    )


def check_claude_skills(r: Report, fix: bool, prefer_copy: bool, refresh_copy: bool) -> None:
    if CLAUDE_SKILLS.is_symlink():
        if CLAUDE_SKILLS.resolve() == SKILLS.resolve():
            if fix and prefer_copy:
                make_copy()
                r.ok(".claude/skills: đã chuyển sang bản copy theo --copy")
            else:
                r.ok(".claude/skills là symlink tới .agents/skills")
            return
        msg = ".claude/skills là symlink nhưng trỏ sai chỗ"
    elif CLAUDE_SKILLS.is_dir():
        if not (CLAUDE_SKILLS / COPY_MARKER).exists():
            r.err(".claude/skills là thư mục do người tạo. Chuyển skill riêng vào .agents/skills, "
                  "xóa thư mục này rồi chạy --fix.")
            return
        if tree_hash(CLAUDE_SKILLS) == tree_hash(SKILLS):
            r.ok(".claude/skills là bản copy, đang khớp .agents/skills")
            return
        if refresh_copy:
            make_copy()
            r.info(".claude/skills: bản copy đã cũ, đã làm mới. Skill mới có hiệu lực từ phiên sau.")
            return
        msg = ".claude/skills là bản copy đã cũ"
    elif CLAUDE_SKILLS.exists():
        msg = ".claude/skills là file thường (symlink bị git checkout hỏng?)"
    else:
        msg = "Thiếu .claude/skills (Claude Code sẽ không thấy skill nào)"

    if not fix:
        r.err(msg + " (chạy lại với --fix)")
        return
    CLAUDE_SKILLS.parent.mkdir(exist_ok=True)
    if prefer_copy:
        make_copy()
        r.ok(msg + " -> đã tạo bản copy")
        return
    try:
        if CLAUDE_SKILLS.is_symlink() or CLAUDE_SKILLS.is_file():
            CLAUDE_SKILLS.unlink()
        elif CLAUDE_SKILLS.is_dir():
            shutil.rmtree(CLAUDE_SKILLS)
        os.symlink(os.path.join("..", ".agents", "skills"), CLAUDE_SKILLS, target_is_directory=True)
        r.ok(msg + " -> đã tạo symlink")
    except OSError as e:
        make_copy()
        r.warn(f"Không tạo được symlink ({e.__class__.__name__}); đã dùng bản copy. Hook SessionStart sẽ tự làm "
               "mới bản copy. Bật Developer Mode của Windows để dùng symlink.")


def _hook_entries() -> dict:
    return {
        "SessionStart": {"hooks": [{"type": "command",
                                    "command": f'"{PY}" "{SCRIPTS}/doctor.py" --session'}]},
        "PreToolUse": {"matcher": "Edit|Write|MultiEdit|Bash|PowerShell",
                       "hooks": [{"type": "command", "command": f'"{PY}" "{SCRIPTS}/guard.py"'}]},
    }


def _is_ours(entry: dict) -> bool:
    return any(".agents/scripts/" in h.get("command", "").replace("\\", "/") for h in entry.get("hooks", []))


def check_claude_hooks(r: Report, fix: bool) -> None:
    try:
        data = json.loads(CLAUDE_LOCAL_SETTINGS.read_text(encoding="utf-8-sig")) if CLAUDE_LOCAL_SETTINGS.exists() else {}
    except json.JSONDecodeError:
        r.err(f"{CLAUDE_LOCAL_SETTINGS} không phải JSON hợp lệ; không đụng vào.")
        return
    wanted = _hook_entries()
    hooks = data.get("hooks", {})
    current_ok = all(
        [e for e in hooks.get(ev, []) if _is_ours(e)] == [want] for ev, want in wanted.items()
    )
    if current_ok:
        r.ok("Hook Claude (SessionStart, PreToolUse guard) đã đăng ký trong .claude/settings.local.json")
        return
    if not fix:
        r.err("Chưa đăng ký hook Claude (guard chặn tự duyệt và lệnh git nguy hiểm). Chạy lại với --fix")
        return
    for ev, want in wanted.items():
        hooks[ev] = [e for e in hooks.get(ev, []) if not _is_ours(e)] + [want]
    data["hooks"] = hooks
    CLAUDE_LOCAL_SETTINGS.parent.mkdir(exist_ok=True)
    CLAUDE_LOCAL_SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    r.ok("Đã đăng ký hook Claude trong .claude/settings.local.json (theo Python của máy này)")


def check_githooks(r: Report, fix: bool) -> None:
    res = git("rev-parse", "--git-path", "hooks")
    if res.returncode != 0:
        r.warn("Không tìm được thư mục git hooks.")
        return
    hooks_dir = (ROOT / res.stdout.strip()).resolve()
    scripts = {
        "pre-commit": f'"{PY}" "{SCRIPTS}/sync.py" --check && "{PY}" "{SCRIPTS}/gate.py" validate',
        "post-merge": f'"{PY}" "{SCRIPTS}/doctor.py" --session >/dev/null 2>&1 || true',
        "post-checkout": f'"{PY}" "{SCRIPTS}/doctor.py" --session >/dev/null 2>&1 || true',
    }
    missing = []
    for name, cmd in scripts.items():
        path = hooks_dir / name
        body = f"#!/bin/sh\n{HOOK_MARKER}: sinh bởi .agents/scripts/doctor.py --fix\n{cmd}\n"
        if path.exists() and HOOK_MARKER not in path.read_text(encoding="utf-8", errors="ignore"):
            r.warn(f"git hook {name} đã có sẵn (không phải của .agents); không ghi đè. Tự thêm: {cmd}")
            continue
        if path.exists() and path.read_text(encoding="utf-8") == body:
            continue
        if fix:
            hooks_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8", newline="\n")
            path.chmod(0o755)
        else:
            missing.append(name)
    if missing:
        r.warn("Chưa cài git hook: " + ", ".join(missing) + " (chạy lại với --fix)")
    else:
        r.ok("git hook pre-commit (sync --check, gate validate), post-merge, post-checkout")


def check_gitignore(r: Report, fix: bool) -> None:
    gi = ROOT / ".gitignore"
    text = read_text(gi) if gi.exists() else ""
    entries = {l.strip().lstrip("/").rstrip("/") for l in text.splitlines()}
    missing = [e for e in GITIGNORE_ENTRIES if e.rstrip("/") not in entries]
    if not missing:
        r.ok(".gitignore có " + ", ".join(GITIGNORE_ENTRIES))
    elif fix:
        sep = "" if text.endswith("\n") or not text else "\n"
        gi.write_text(text + sep + "\n# .agents\n" + "\n".join(missing) + "\n", encoding="utf-8", newline="\n")
        r.ok(".gitignore: đã thêm " + ", ".join(missing))
    else:
        r.warn(".gitignore thiếu: " + ", ".join(missing) + " (chạy lại với --fix)")


def session_status() -> None:
    import gate
    ids = _lib.infer_task_ids()
    if len(ids) == 1:
        print(f"Task hiện tại theo tên nhánh: {ids[0]}")
        gate.print_status(ROOT / _lib.WORK / ids[0])
    elif len(ids) > 1:
        print("Các nhánh đang trỏ tới nhiều task: " + ", ".join(ids))


def main(argv: list[str]) -> int:
    fix, prefer_copy = "--fix" in argv, "--copy" in argv
    session, ci = "--session" in argv, "--ci" in argv
    r = Report(quiet="--quiet" in argv or session)
    if not r.quiet:
        print(f"Kiểm tra bộ .agents tại {ROOT}\n")
    check_python(r)
    check_openpyxl(r)
    check_root(r)
    check_submodules(r, ci)
    names = check_skills(r)
    check_forbidden(r)
    check_agents_md(r, fix)
    check_claude_md(r)
    if not ci:
        check_personal_conflicts(r, names)
        check_claude_skills(r, fix, prefer_copy, refresh_copy=fix or session)
        check_claude_hooks(r, fix)
        check_githooks(r, fix)
    check_gitignore(r, fix)
    if session and (r.errors or r.warnings):
        print("[.agents doctor] Môi trường quy trình có vấn đề; báo người dùng trước khi làm task:")
    r.flush()
    if session:
        session_status()
        return 0
    if not r.quiet or r.errors or r.warnings:
        print(f"\nKết quả: {r.errors} lỗi, {r.warnings} cảnh báo.")
    if r.errors == 0 and not r.quiet:
        print("Bước cuối (làm tay, một lần mỗi tool): mở agent ở gốc repo và hỏi "
              "'liệt kê các skill bạn đang thấy'. Phải có wf-requirement.")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
