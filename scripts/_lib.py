"""Hàm dùng chung cho các script trong .agents/scripts. Chỉ dùng thư viện chuẩn.

- Tìm gốc superproject (ROOT), đọc .gitmodules và vai trò submodule trong AGENTS.md.
- Một parser frontmatter duy nhất: bỏ BOM, chuẩn hóa CRLF, key chữ thường, bỏ comment và dấu nháy,
  hỗ trợ một mức map lồng nhau (dùng cho `inputs:`), báo lỗi rõ khi gặp YAML nhiều dòng.
- Hash nội dung artifact (bỏ các trường duyệt) để phát hiện approval đã cũ.
- Suy ra task ID từ tên nhánh.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # tiếng Việt trên console Windows
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

AGENTS_DIR = Path(__file__).resolve().parents[1]
# AGENTS_ROOT cho phép test chạy trên thư mục tạm.
ROOT = Path(os.environ.get("AGENTS_ROOT") or AGENTS_DIR.parent).resolve()
WORK = "work"

STAGES = [
    ("requirement", "01-requirement.md"),
    ("contract", "02-contract.md"),
    ("plan", "03-plan.md"),
    ("implement", "04-impl-notes.md"),
    ("test", "05-test-report.md"),
    ("review", "06-review.md"),
]
STAGE_NAMES = [s for s, _ in STAGES]
ARTIFACT = dict(STAGES)
APPROVAL_KEYS = ("status", "approved_by", "approved_at", "content_hash", "inputs")
BRANCH_TYPES = ("feat", "fix", "refactor", "test", "docs", "chore")
MULTILINE_MARKERS = {">", "|", ">-", "|-", ">+", "|+"}


# ---------------------------------------------------------------- git

def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-c", "core.quotepath=false", *args],
            cwd=cwd or ROOT, capture_output=True, text=True, encoding="utf-8",
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(args, 127, "", "git not found")


def git_user() -> str:
    return git("config", "user.name").stdout.strip()


def submodules(root: Path | None = None) -> list[dict[str, str]]:
    """Đọc .gitmodules trực tiếp (không phụ thuộc git, không vỡ khi đường dẫn có dấu cách)."""
    path = (root or ROOT) / ".gitmodules"
    if not path.exists():
        return []
    items: list[dict[str, str]] = []
    cur: dict[str, str] | None = None
    for line in read_text(path).split("\n"):
        line = line.strip()
        m = re.match(r'^\[submodule\s+"(.+)"\]$', line)
        if m:
            cur = {"name": m.group(1)}
            items.append(cur)
        elif cur is not None and "=" in line:
            k, v = line.split("=", 1)
            cur[k.strip().lower()] = v.strip()
    return [i for i in items if "path" in i]


def base_branch(sm_path: str, root: Path | None = None) -> str:
    for sm in submodules(root):
        if sm["path"] == sm_path and sm.get("branch"):
            return sm["branch"]
    return "main"


# ---------------------------------------------------------------- AGENTS.md

def project_roles(root: Path | None = None) -> dict[str, list[str]]:
    """Đọc mục "Vai trò submodule" trong AGENTS.md, dạng:  - contract: `api_contract`

    Giá trị là tiền tố đường dẫn tính từ gốc superproject; nhiều giá trị cách nhau bằng dấu phẩy.
    """
    path = (root or ROOT) / "AGENTS.md"
    if not path.exists():
        return {}
    roles: dict[str, list[str]] = {}
    for line in read_text(path).split("\n"):
        m = re.match(r"^\s*[-*]\s*(contract|integration-test|client|backend|docs)\s*:\s*(.+)$", line)
        if m:
            vals = re.findall(r"`([^`]+)`", m.group(2))
            if vals:
                roles[m.group(1)] = [v.strip().strip("/") for v in vals]
    return roles


# ---------------------------------------------------------------- frontmatter

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def _clean_value(v: str) -> str:
    v = v.strip()
    q = v[:1]
    if q in ("'", '"'):
        end = v.find(q, 1)
        if end > 0:
            return v[1:end]
    return re.split(r"\s+#", v, maxsplit=1)[0].strip()


def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    """Trả về (các dòng frontmatter hoặc None, phần thân)."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def parse_frontmatter(text: str) -> tuple[dict, list[str]]:
    """Trả về (dữ liệu, danh sách lỗi). Map lồng nhau một mức được trả về dạng dict."""
    fm_lines, _ = split_frontmatter(text)
    if fm_lines is None:
        if text.lstrip("﻿").startswith("---"):
            return {}, ["frontmatter thiếu dòng '---' đóng"]
        return {}, []
    data: dict = {}
    errors: list[str] = []
    parent: str | None = None
    for raw in fm_lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t"):
            if parent is None:
                errors.append(f"dòng thụt lề không thuộc key nào: {raw.strip()!r}")
                continue
            if ":" not in raw:
                errors.append(f"dòng lồng trong '{parent}' không có dạng key: value: {raw.strip()!r}")
                continue
            k, v = raw.split(":", 1)
            if not isinstance(data.get(parent), dict):
                data[parent] = {}
            data[parent][k.strip()] = _clean_value(v)
            continue
        if ":" not in raw:
            errors.append(f"dòng không có dạng key: value: {raw.strip()!r}")
            parent = None
            continue
        k, v = raw.split(":", 1)
        key = k.strip().lower()
        val = _clean_value(v)
        if v.strip() in MULTILINE_MARKERS:
            errors.append(f"'{key}' dùng YAML nhiều dòng ({v.strip()}); hãy viết trên một dòng")
            val = ""
        data[key] = val
        parent = key if val == "" else None
    return data, errors


def read_frontmatter(path: Path) -> dict:
    return parse_frontmatter(read_text(path))[0]


def content_hash(text: str) -> str:
    """Hash nội dung artifact, không tính các trường duyệt; bỏ qua khác biệt khoảng trắng cuối dòng."""
    fm_lines, body = split_frontmatter(text)
    kept: list[str] = []
    skipping = False
    for raw in fm_lines or []:
        if raw[:1] in (" ", "\t"):
            if not skipping and raw.strip():
                kept.append(raw.rstrip())
            continue
        skipping = False
        key = raw.split(":", 1)[0].strip().lower() if ":" in raw else ""
        if key in APPROVAL_KEYS:
            skipping = True
            continue
        if raw.strip():
            kept.append(raw.rstrip())
    body_lines = [l.rstrip() for l in body.split("\n")]
    norm = "\n".join(kept) + "\n---\n" + "\n".join(body_lines).strip("\n")
    return "sha256:" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def set_frontmatter_fields(text: str, fields: dict, drop: tuple[str, ...] = ()) -> str:
    """Ghi các trường vào frontmatter. Xóa trước các key trong `drop` (kèm dòng lồng của chúng).
    Giá trị là dict thì ghi thành map lồng một mức."""
    fm_lines, body = split_frontmatter(text)
    if fm_lines is None:
        raise ValueError("artifact không có frontmatter")
    remove = set(drop) | set(fields)
    out: list[str] = []
    skipping = False
    for raw in fm_lines:
        if raw[:1] in (" ", "\t") and skipping:
            continue
        skipping = False
        key = raw.split(":", 1)[0].strip().lower() if ":" in raw and raw[:1] not in (" ", "\t") else ""
        if key in remove:
            skipping = True
            continue
        out.append(raw)
    while out and not out[-1].strip():
        out.pop()
    for k, v in fields.items():
        if isinstance(v, dict):
            out.append(f"{k}:")
            out.extend(f"  {ik}: {iv}" for ik, iv in v.items())
        else:
            out.append(f"{k}: {v}")
    return "---\n" + "\n".join(out) + "\n---\n" + body


# ---------------------------------------------------------------- task

def task_id_from_branch(branch: str) -> str:
    branch = branch.strip()
    if "/" in branch and branch.split("/", 1)[0] in BRANCH_TYPES:
        return branch.split("/", 1)[1]
    return branch


def infer_task_ids(root: Path | None = None) -> list[str]:
    """Task ID suy từ nhánh hiện tại của superproject và các submodule, chỉ giữ ID có work/<id>/."""
    root = root or ROOT
    found: list[str] = []
    for p in [root] + [root / sm["path"] for sm in submodules(root)]:
        if not p.exists():
            continue
        br = git("branch", "--show-current", cwd=p).stdout.strip()
        if not br:
            continue
        tid = task_id_from_branch(br)
        if (root / WORK / tid).is_dir() and tid not in found:
            found.append(tid)
    return found


def resolve_task_dir(arg: str | None, root: Path | None = None) -> Path:
    """`1.10-x`, `work/1.10-x` hay đường dẫn tuyệt đối đều được; luôn tính từ gốc superproject."""
    root = root or ROOT
    if arg is None:
        ids = infer_task_ids(root)
        if len(ids) == 1:
            return root / WORK / ids[0]
        if not ids:
            raise LookupError("Không suy ra được task ID từ tên nhánh. Hãy truyền task ID.")
        raise LookupError("Các nhánh đang trỏ tới nhiều task khác nhau: " + ", ".join(ids)
                          + ". Hãy truyền task ID.")
    p = Path(arg)
    if p.is_absolute():
        return p
    if len(p.parts) == 1:
        return root / WORK / p
    return root / p
