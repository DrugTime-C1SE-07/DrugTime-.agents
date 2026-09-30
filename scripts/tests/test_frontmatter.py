from _lib import content_hash, parse_frontmatter, set_frontmatter_fields


def test_bom_crlf_and_uppercase_key():
    fm, errs = parse_frontmatter("﻿---\r\nStatus: approved\r\n---\r\nbody")
    assert errs == [] and fm["status"] == "approved"


def test_comment_and_quotes():
    fm, _ = parse_frontmatter("---\nstatus: 'draft'  # ghi chú\nsize: S # nhỏ\n---\n")
    assert fm["status"] == "draft" and fm["size"] == "S"


def test_multiline_yaml_is_an_error_not_a_value():
    fm, errs = parse_frontmatter("---\nname: x\ndescription: >\n  dài\n---\n")
    assert errs and fm["description"] != ">"


def test_nested_inputs_map():
    fm, errs = parse_frontmatter("---\nstatus: approved\ninputs:\n  01-requirement.md: sha256:ab\n---\n")
    assert errs == [] and fm["inputs"] == {"01-requirement.md": "sha256:ab"}


def test_hash_ignores_approval_fields_and_trailing_spaces():
    a = "---\ntask: t\nstatus: draft\n---\nxin chào\n"
    b = "---\ntask: t\nstatus: approved\napproved_by: A\ninputs:\n  x: y\n---\nxin chào   \n\n"
    assert content_hash(a) == content_hash(b)


def test_hash_changes_with_content_and_decision_fields():
    base = "---\ntask: t\ncontract_change: no\n---\nA\n"
    assert content_hash(base) != content_hash(base.replace("A", "B"))
    assert content_hash(base) != content_hash(base.replace("no", "yes"))


def test_set_fields_replaces_nested_block():
    t = "---\ntask: t\nstatus: approved\ninputs:\n  a: 1\nsize: M\n---\nbody"
    out = set_frontmatter_fields(t, {"status": "draft"}, drop=("inputs",))
    assert "inputs" not in out and "size: M" in out and out.endswith("body")
