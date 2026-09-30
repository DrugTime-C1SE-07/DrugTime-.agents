import gate
import guard
from conftest import artifact


def test_blocks_writing_approval_fields(root):
    p = root / "work" / "t1" / "01-requirement.md"
    reason = guard.check_edit({"file_path": str(p), "content": "---\nstatus: approved\n---\n"}, None)
    assert reason and "approve" in reason


def test_allows_drafts_and_empty_fields(root):
    p = root / "work" / "t1" / "01-requirement.md"
    content = "---\nstatus: draft\napproved_by:\n---\n"
    assert guard.check_edit({"file_path": str(p), "content": content}, None) is None


def test_blocks_editing_approved_artifact(root):
    t = root / "work" / "t1"
    artifact(t, "01-requirement.md", "size: M\ncontract_change: no\n")
    gate.do_approve(t, "requirement", "A", "now")
    reason = guard.check_edit({"file_path": str(t / "01-requirement.md"), "old_string": "a", "new_string": "b"}, None)
    assert reason and "reopen" in reason


def test_ignores_files_outside_work(root):
    assert guard.check_edit({"file_path": str(root / "backend" / "x.py"), "content": "status: approved"}, None) is None


def test_blocks_skill_copy_edit(root):
    assert guard.check_edit({"file_path": str(root / ".claude" / "skills" / "wf-plan" / "SKILL.md")}, None)


def test_dangerous_commands():
    bad = ["git push --force", "git -C backend push -f origin x", "git push origin +main",
           "git reset --hard HEAD~1", "git clean -fd", "git branch -D feat/x",
           "git submodule update --remote", "python .agents/scripts/gate.py approve t1 plan",
           "git push origin --delete feat/x"]
    for cmd in bad:
        assert guard.check_command(cmd), cmd


def test_safe_commands():
    ok = ["git push -u origin feat/1.10-x", "git status", "git -C backend diff main...HEAD",
          "python .agents/scripts/gate.py t1 plan", "git submodule update --init --recursive",
          "git reset HEAD file.py", "git branch --show-current",
          "python .agents/scripts/gate.py reopen t1 plan"]
    for cmd in ok:
        assert guard.check_command(cmd) is None, cmd
