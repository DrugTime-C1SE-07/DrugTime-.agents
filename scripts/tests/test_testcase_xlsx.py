import copy
import json

import pytest

openpyxl = pytest.importorskip("openpyxl")

import _lib  # noqa: E402
import scope  # noqa: E402
import testcase_xlsx as tx  # noqa: E402
from conftest import write  # noqa: E402


def case(cid, status="Pass", **kw):
    c = {"id": cid, "description": f"mô tả {cid}", "precondition": "API đang chạy",
         "steps": ["Gửi POST /auth/login", "Đọc response"], "data": "a@b.vn / 123456",
         "expected": "200, có access_token", "actual": "200, có access_token" if status != "Pending" else "",
         "status": status, "comments": "AC1 · EP (1,2)"}
    if status == "Fail":
        c.update(actual="500", severity="High", root_cause="thiếu kiểm tra null", evidence="evidence/x.log")
    c.update(kw)
    return c


def spec(code="AUTH", sheet="Login", cases=None, **kw):
    f = {"code": code, "name": "Đăng nhập", "sheet": sheet, "created_by": "Nguyen",
         "created_date": "2026-10-07", "priority": "High", "description": "Xác thực",
         "ep": [{"field": "Email", "valid": ["đúng định dạng"], "invalid": ["rỗng", "sai định dạng"]},
                {"field": "Password", "valid": ["8–64 ký tự"], "invalid": ["< 8 ký tự"]}],
         "decision_tables": [{"title": "Đăng nhập", "conditions": [
             {"name": "Email hợp lệ?", "values": ["No", "Yes", "Yes"]},
             {"name": "Khớp DB?", "values": ["-", "No", "Yes"]}],
             "actions": [{"name": "422", "rules": [1]}, {"name": "401", "rules": [2]}, {"name": "200", "rules": [3]}]}],
         "cases": cases or [case(f"TC-{code}-01"), case(f"TC-{code}-02", "Fail"), case(f"TC-{code}-03", "Pending")]}
    f.update(kw)
    return {"project": "DrugTime", "functions": [f]}


# ---------------------------------------------------------------- validate

def test_valid_spec_has_no_errors():
    assert tx.validate(spec()) == []


@pytest.mark.parametrize("mutate, needle", [
    (lambda c: c.update(id="TC-XX-01"), "id phải có dạng"),
    (lambda c: c.update(status="Done"), "'status' phải"),
    (lambda c: c.update(status="Pending"), "Pending nghĩa là chưa chạy"),
    (lambda c: c.update(actual=""), "cần 'actual'"),
    (lambda c: c.update(comments=""), "thiếu 'comments'"),
    (lambda c: c.update(steps=[]), "'steps'"),
])
def test_case_rules(mutate, needle):
    s = spec()
    mutate(s["functions"][0]["cases"][0])
    assert any(needle in e for e in tx.validate(s)), tx.validate(s)


def test_fail_needs_severity_and_root_cause():
    s = spec(cases=[case("TC-AUTH-01", "Fail", severity="Blocker", root_cause="")])
    errs = tx.validate(s)
    assert any("severity" in e for e in errs) and any("root_cause" in e for e in errs)


def test_duplicate_ids_and_reserved_sheet():
    s = spec(sheet="Report", cases=[case("TC-AUTH-01"), case("TC-AUTH-01")])
    errs = tx.validate(s)
    assert any("trùng id" in e for e in errs) and any("dành cho báo cáo" in e for e in errs)


def test_decision_table_rule_out_of_range():
    s = spec()
    s["functions"][0]["decision_tables"][0]["actions"][0]["rules"] = [4]
    assert any("ngoài 1..3" in e for e in tx.validate(s))


# ---------------------------------------------------------------- build

def test_build_layout(tmp_path):
    out = tmp_path / "t.xlsx"
    tx.apply(spec(), out, fresh=True)
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Login", "Report"]
    ws = wb["Login"]
    assert [ws.cell(r, 1).value for r in range(1, 7)] == tx.INFO
    assert ws["B2"].value == "Đăng nhập (AUTH)"
    assert [ws.cell(8, c).value for c in range(1, 10)] == tx.HEADERS
    assert ws["A9"].value == "TC-AUTH-01"
    assert ws["D9"].value == "1. Gửi POST /auth/login\n2. Đọc response"
    assert ws["G11"].value in (None, "")  # Pending không có actual
    assert ws.freeze_panes == "A9"
    assert ws["G14"].value == "Pass" and ws["H14"].value == '=COUNTIF(H9:H11,"Pass")'
    assert ws["H17"].value == "=SUM(H14:H16)"
    assert any("H9:H11" in str(cf.sqref) for cf in ws.conditional_formatting)
    # bảng EP: lớp hợp lệ đánh số trước (1, 2), lớp không hợp lệ sau (3, 4, 5)
    assert ws["K8"].value == "Field" and ws["M9"].value == "1" and ws["O9"].value == "3\n4"
    assert ws["O10"].value == "5"
    # bảng quyết định ở cột Q: điều kiện rồi hành động, X đánh dấu rule
    assert ws["Q8"].value == "Rule" and ws["R8"].value == "R1" and ws["R9"].value == "No"
    assert ws["Q11"].value == "Action" and ws["R12"].value == "X" and ws["T14"].value == "X"
    rep = wb["Report"]
    bug_hdr = next(r for r in range(1, rep.max_row + 1) if rep.cell(r, 1).value == "Bug ID")
    assert rep.cell(bug_hdr + 1, 1).value == "BUG-AUTH-02"
    assert rep.cell(bug_hdr + 1, 7).value == "High"
    assert "Log: evidence/x.log" in rep.cell(bug_hdr + 1, 9).value
    func_hdr = next(r for r in range(1, rep.max_row + 1) if rep.cell(r, 1).value == "Function")
    assert rep.cell(func_hdr + 1, 3).value == "Login"
    assert "'Login'!$H$17" in rep.cell(func_hdr + 1, 5).value or "Login!$H$17" in rep.cell(func_hdr + 1, 5).value


# ---------------------------------------------------------------- merge

def test_merge_replaces_only_its_function(tmp_path):
    book = tmp_path / "book.xlsx"
    wb = openpyxl.Workbook()
    wb.active.title = "Trang_tính1"  # sheet trống mặc định: bị bỏ
    wb.save(book)

    a = spec()
    b = spec(code="DOSE", sheet="Dose log", priority="Medium", description="Ghi liều",
             cases=[case("TC-DOSE-01", "Fail"), case("TC-DOSE-02")])
    assert tx.apply(a, book, fresh=False) == []
    tx.apply(b, book, fresh=False)
    wb = openpyxl.load_workbook(book)
    assert wb.sheetnames == ["Login", "Dose log", "Report"]

    a2 = copy.deepcopy(a)
    a2["functions"][0]["cases"][1] = case("TC-AUTH-02")  # bug đã sửa
    a2["functions"][0]["cases"].pop(0)                    # TC-AUTH-01 bị bỏ khỏi spec
    warnings = tx.apply(a2, book, fresh=False)
    assert any("TC-AUTH-01" in w for w in warnings)

    wb = openpyxl.load_workbook(book)
    assert wb.sheetnames == ["Login", "Dose log", "Report"]
    rep = wb["Report"]
    ids = [rep.cell(r, 1).value for r in range(1, rep.max_row + 1)]
    assert "BUG-AUTH-02" not in ids and "BUG-DOSE-01" in ids
    func_hdr = ids.index("Function") + 1
    row = {rep.cell(r, 3).value: r for r in range(func_hdr + 1, func_hdr + 3)}
    assert rep.cell(row["Dose log"], 7).value == "Medium"       # meta chức năng khác được giữ
    assert rep.cell(row["Dose log"], 2).value == "Ghi liều"


def test_merge_refuses_foreign_sheet_with_same_name(tmp_path):
    book = tmp_path / "book.xlsx"
    wb = openpyxl.Workbook()
    wb.active.title = "Login"
    wb.active["A1"] = "dữ liệu khác"
    wb.save(book)
    with pytest.raises(ValueError):
        tx.apply(spec(), book, fresh=False)


# ---------------------------------------------------------------- CLI, vai trò, phạm vi

def test_cli_build_and_merge_default_book(root):
    write(root / "AGENTS.md", "### Vai trò submodule\n\n- testcase-book: `docs/qa/Test_Cases.xlsx`\n")
    t = root / "work" / "t1"
    write(t / "testcases.json", json.dumps(spec(), ensure_ascii=False))
    assert tx.main(["x", "build", "t1"]) == 0
    assert (t / "testcases.xlsx").exists()
    assert tx.main(["x", "merge", "t1"]) == 0
    assert (root / "docs" / "qa" / "Test_Cases.xlsx").exists()


def test_cli_rejects_invalid_spec(root):
    t = root / "work" / "t2"
    bad = spec(cases=[case("TC-AUTH-01", "Pending", actual="có kết quả")])
    write(t / "testcases.json", json.dumps(bad, ensure_ascii=False))
    assert tx.main(["x", "build", "t2"]) == 1
    assert not (t / "testcases.xlsx").exists()


def test_role_and_scope():
    roles = {"integration-test": ["tests"], "testcase-book": ["docs/qa/Test_Cases.xlsx"]}
    res = scope.evaluate("t1", "test", ["docs/qa/Test_Cases.xlsx", "docs/other.md"], [], roles)
    assert res["outside"] == ["docs/other.md"]
    res = scope.evaluate("t1", "implement", ["docs/qa/Test_Cases.xlsx"], [], roles)
    assert res["outside"] == []


def test_project_roles_reads_testcase_book(root):
    write(root / "AGENTS.md", "- testcase-book: `docs/Team/04_Quality_&_Testing/Test_Cases.xlsx`\n")
    assert _lib.project_roles(root)["testcase-book"] == ["docs/Team/04_Quality_&_Testing/Test_Cases.xlsx"]
