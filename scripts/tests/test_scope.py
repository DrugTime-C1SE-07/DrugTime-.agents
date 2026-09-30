import scope
from conftest import artifact

PLAN = """
## 3. File sẽ thay đổi (ranh giới phạm vi)

| Submodule | Đường dẫn | Thêm / sửa / xóa | Mục đích |
|---|---|---|---|
| backend | `src/drugtime/modules/auth/**` | thêm | module |
| backend | `backend/tests/unit/test_auth.py` | thêm | test |
| tests | `test_auth_flow.py` | thêm | tích hợp |

## 4. Checklist
"""
ROLES = {"integration-test": ["tests", "backend/tests/integration"], "contract": ["api_contract"]}


def test_plan_entries_prefix_and_glob(root):
    t = root / "work" / "t1"
    artifact(t, "03-plan.md", body=PLAN)
    entries = scope.plan_entries(t)
    assert "backend/src/drugtime/modules/auth/**" in entries
    assert "backend/tests/unit/test_auth.py" in entries
    assert "tests/test_auth_flow.py" in entries


def test_implement_scope():
    plan = ["backend/src/drugtime/modules/auth/**", "backend/tests/unit/test_auth.py", "tests/test_auth_flow.py"]
    changed = ["backend/src/drugtime/modules/auth/api.py", "backend/src/drugtime/main.py",
               "tests/test_auth_flow.py", "work/t1/04-impl-notes.md"]
    res = scope.evaluate("t1", "implement", changed, plan, ROLES)
    assert res["outside"] == ["backend/src/drugtime/main.py", "tests/test_auth_flow.py"]
    assert res["untouched"] == ["backend/tests/unit/test_auth.py"]


def test_test_stage_only_integration_area():
    changed = ["backend/tests/integration/test_x.py", "tests/a.py", "backend/src/x.py"]
    res = scope.evaluate("t1", "test", changed, [], ROLES)
    assert res["outside"] == ["backend/src/x.py"]


def test_analysis_stages_touch_nothing():
    res = scope.evaluate("t1", "requirement", ["work/t1/01-requirement.md", "backend/x.py"], [], ROLES)
    assert res["outside"] == ["backend/x.py"]


def test_small_task_reads_scope_from_requirement(root):
    t = root / "work" / "t1"
    artifact(t, "01-requirement.md", "size: S\ncontract_change: no\n", body=PLAN)
    assert "tests/test_auth_flow.py" in scope.plan_entries(t)
