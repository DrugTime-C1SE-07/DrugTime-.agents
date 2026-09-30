"""Chạy: python -m pytest .agents/scripts/tests -q  (từ gốc superproject)."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Phải đặt trước khi import script: _lib đọc AGENTS_ROOT lúc import.
FAKE_ROOT = Path(tempfile.mkdtemp(prefix="agents-root-")).resolve()
os.environ["AGENTS_ROOT"] = str(FAKE_ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def root():
    work = FAKE_ROOT / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    yield FAKE_ROOT


def write(path: Path, text: str, bom: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\n", "\r\n").encode("utf-8") if bom else text.encode("utf-8")
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)
    return path


def artifact(task_dir: Path, name: str, extra: str = "", body: str = "nội dung", bom: bool = False) -> Path:
    return write(task_dir / name,
                 f"---\ntask: {task_dir.name}\nstatus: draft\n{extra}---\n\n# {name}\n\n{body}\n", bom)
