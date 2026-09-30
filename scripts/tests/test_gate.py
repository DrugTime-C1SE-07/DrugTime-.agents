import pytest

import gate
from _lib import resolve_task_dir
from conftest import artifact

NOW = "2026-09-30 10:00 +0700"


def mk_task(root, size="M", cc="no"):
    t = root / "work" / "t1"
    artifact(t, "01-requirement.md", f"size: {size}\ncontract_change: {cc}\n")
    return t


def approve(t, stage):
    gate.do_approve(t, stage, "Người duyệt", NOW)


def test_requirement_needs_size_and_contract(root):
    t = root / "work" / "t1"
    artifact(t, "01-requirement.md", "contract_change: unknown\n")
    probs = gate.check(t, "plan", current_user="")
    assert any("contract_change" in p for p in probs) and any("size" in p for p in probs)


def test_happy_path_and_block_on_draft(root):
    t = mk_task(root)
    assert gate.check(t, "plan", current_user="") != []
    approve(t, "requirement")
    assert gate.check(t, "plan", current_user="") == []


def test_manual_approved_without_fields_is_rejected(root):
    t = mk_task(root)
    p = t / "01-requirement.md"
    p.write_text(p.read_text(encoding="utf-8").replace("status: draft", "status: approved"), encoding="utf-8")
    assert any("gate.py approve" in x for x in gate.check(t, "plan", current_user=""))


def test_edit_after_approval_is_detected(root):
    t = mk_task(root)
    approve(t, "requirement")
    p = t / "01-requirement.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nthêm dòng\n", encoding="utf-8")
    assert any("bị sửa sau khi duyệt" in x for x in gate.check(t, "plan", current_user=""))


def test_stale_downstream_after_reopen_and_reapprove(root):
    """Kịch bản trong review: 04 sửa và duyệt lại thì 05 cũ phải hết hiệu lực."""
    t = mk_task(root)
    approve(t, "requirement")
    artifact(t, "03-plan.md")
    approve(t, "plan")
    artifact(t, "04-impl-notes.md")
    approve(t, "implement")
    artifact(t, "05-test-report.md")
    approve(t, "test")
    assert gate.check(t, "review", current_user="") == []
    gate.do_reopen(t, "implement")
    p = t / "04-impl-notes.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nsửa lỗi review\n", encoding="utf-8")
    approve(t, "implement")
    probs = gate.check(t, "review", current_user="")
    assert any("05-test-report.md" in x and "Cần duyệt lại" in x for x in probs)
    assert "ĐÃ CŨ" in gate.label_of(t, "test")


def test_reapprove_without_content_change_keeps_downstream_valid(root):
    t = mk_task(root)
    approve(t, "requirement")
    artifact(t, "03-plan.md")
    approve(t, "plan")
    gate.do_reopen(t, "requirement")
    approve(t, "requirement")
    assert gate.check(t, "implement", current_user="") == []


def test_cannot_approve_on_top_of_unapproved_input(root):
    t = mk_task(root)
    artifact(t, "03-plan.md")
    with pytest.raises(ValueError, match="01-requirement.md"):
        approve(t, "plan")


def test_small_task_fast_lane(root):
    t = mk_task(root, size="S")
    assert gate.flow(t) == ["requirement", "implement", "review"]
    approve(t, "requirement")
    assert gate.check(t, "implement", current_user="") == []
    assert "không có giai đoạn" in gate.check(t, "plan", current_user="")[0]


def test_small_task_cannot_change_contract(root):
    t = mk_task(root, size="S", cc="yes")
    assert any("size S" in p for p in gate.check(t, "implement", current_user=""))


def test_contract_stage_only_when_yes(root):
    t = mk_task(root, cc="yes")
    approve(t, "requirement")
    assert gate.check(t, "plan", current_user="") != []
    artifact(t, "02-contract.md")
    approve(t, "contract")
    assert gate.check(t, "plan", current_user="") == []


def test_owner_mismatch_blocks_implement(root):
    t = mk_task(root)
    approve(t, "requirement")
    artifact(t, "03-plan.md")
    approve(t, "plan")
    artifact(t, "04-impl-notes.md", "owner: An\n")
    assert any("An" in p for p in gate.check(t, "implement", current_user="Bình"))
    assert gate.check(t, "implement", current_user="An") == []


def test_bom_file_is_read(root):
    t = root / "work" / "t1"
    artifact(t, "01-requirement.md", "size: M\ncontract_change: no\n", bom=True)
    assert gate.requirement_problems(t) == []


def test_validate_flags_edit_after_approval(root):
    t = mk_task(root)
    approve(t, "requirement")
    p = t / "01-requirement.md"
    p.write_text(p.read_text(encoding="utf-8").replace("nội dung", "đã đổi"), encoding="utf-8")
    errors, _ = gate.validate(root)
    assert any("bị sửa sau khi duyệt" in e for e in errors)


def test_resolve_is_relative_to_root_not_cwd(root, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert resolve_task_dir("work/t9") == root / "work" / "t9"
    assert resolve_task_dir("t9") == root / "work" / "t9"
