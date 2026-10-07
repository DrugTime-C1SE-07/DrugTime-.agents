---
name: wf-testcase
description: Viết bộ test case Excel chi tiết cho chức năng vừa làm xong — thiết kế test case bằng phân lớp tương đương, giá trị biên, bảng quyết định, chuyển trạng thái, đoán lỗi; ghi spec work/<task-id>/testcases.json, dựng work/<task-id>/testcases.xlsx và gộp vào file test case tổng của dự án, kèm Bug Report và Test Report. Dùng ở cuối wf-test (task size S thì ở cuối wf-implement), hoặc khi người dùng nói "viết test case", "file excel test case", "test case + bug report", "cập nhật file test case", "báo cáo test".
---

# Bộ test case Excel

## Vai trò

Tester viết tài liệu kiểm thử của chức năng.

- **Chịu trách nhiệm**: mỗi chức năng làm xong có bộ test case đủ chi tiết để người khác chạy lại bằng tay, và mỗi kết quả trong file truy được về lần chạy thật.
- **Ưu tiên khi mâu thuẫn**: trung thực về kết quả > phủ vùng rủi ro và tiêu chí chấp nhận > đúng định dạng mẫu > số lượng test case.
- **Mặc định**: test case chưa chạy trong phiên này là `Pending`; không suy ra `Pass` từ việc "code trông đúng".
- **Không làm**: tự viết file `.xlsx` bằng tay hay bằng code khác ngoài script; sửa code sản phẩm; đổi `Fail` thành `Pass` cho đẹp báo cáo.

## Định dạng (theo file mẫu của team)

Mỗi chức năng là một sheet:

- Dòng 1–6: Project Name, Module Name (`<tên chức năng> (<MÃ>)`), Created By, Creation Date, Reviewed By, Reviewed Date.
- Dòng 8: `Test Case ID | Description | Precondition | Test Steps | Test Data | Expected Result | Actual Result | Status | Comments(if any)`.
- Dưới bảng: khối tổng Pass, Fail, Pending, Total bằng công thức.
- Bên phải: bảng phân lớp tương đương (cột K) và bảng quyết định (cột Q), là căn cứ cho các tham chiếu ở cột Comments.

Sheet `Report` cuối file: tổng theo người viết, bảng theo chức năng (% Executed, % Passed, % Failed, Priority, Remarks), biểu đồ, và **Bug Report** sinh từ các test case `Fail`. Script dựng toàn bộ định dạng; agent chỉ viết spec.

Tiêu đề cột giữ tiếng Anh như mẫu; nội dung viết tiếng Việt; thông báo của hệ thống (message lỗi, mã trạng thái, text trên màn hình) chép nguyên văn.

## Các bước

### 1. Xác định chức năng và mã

Một task có thể chạm một hay nhiều chức năng; mỗi chức năng một mục trong `functions`. Mã chức năng (`code`) viết hoa, ngắn, ổn định giữa các task, vì script dùng mã để tìm và thay sheet cũ trong file tổng. Mở file tổng (vai trò `testcase-book` trong `AGENTS.md`) xem chức năng đã có mã chưa; có rồi thì dùng lại mã và tên sheet đó, và đọc test case cũ để giữ những test case vẫn còn đúng.

### 2. Thiết kế test case

Đọc AC trong `01`, contract trong `02` (nếu có), các test đã viết ở giai đoạn implement và test. Lần lượt áp dụng:

1. **Phân lớp tương đương (EP)**: với mỗi trường input, liệt kê lớp hợp lệ và không hợp lệ trong `ep`. Script đánh số lớp hợp lệ trước, lớp không hợp lệ sau (ví dụ hợp lệ 1–2, không hợp lệ 3–7); mỗi lớp có ít nhất một test case, Comments ghi `EP (1,4)`.
2. **Giá trị biên (BVA)**: với mỗi giới hạn (độ dài, khoảng số, ngày giờ): min−1, min, max, max+1. Comments ghi `BVA (min-1)`.
3. **Bảng quyết định**: khi kết quả phụ thuộc tổ hợp điều kiện (ví dụ có liên kết × consent còn hiệu lực). Mỗi rule một test case, Comments ghi `Decision Table (R2)`.
4. **Chuyển trạng thái**: với đối tượng có vòng đời (liều Chờ → Đã uống / Bỏ lỡ → Uống trễ), phủ mỗi chuyển hợp lệ và ít nhất một chuyển bị cấm.
5. **Đoán lỗi và bảo mật**: rỗng, chỉ khoảng trắng, Unicode/emoji, chuỗi rất dài, ký tự SQL/HTML, gửi trùng, bấm liên tục, mất mạng, token hết hạn, truy cập dữ liệu của người khác.

Bắt buộc có test case cho:

- Mọi AC của task (Comments ghi mã AC).
- Mọi kịch bản trong "Kịch bản chất lượng cho test tích hợp" của `AGENTS.md` ứng với vùng rủi ro task chạm.
- Mọi lỗi sản phẩm tìm thấy ở giai đoạn test.

Viết từng test case sao cho người không đọc code chạy lại được:

- **Description**: một hành vi, bắt đầu bằng động từ ("Xác nhận liều với client_uuid đã dùng").
- **Precondition**: trạng thái dữ liệu và người dùng trước khi chạy.
- **Test Steps**: danh sách bước cụ thể (endpoint và method, hoặc màn hình và nút bấm); script tự đánh số.
- **Test Data**: giá trị cụ thể, không viết "dữ liệu hợp lệ". Dùng `(blank)` cho rỗng, `a*256` cho chuỗi dài.
- **Expected Result**: kết quả quan sát được (mã trạng thái, message nguyên văn, dòng trong DB, dòng `access_logs`).
- **Comments**: `<mã AC> · <kỹ thuật> (<tham chiếu>)`, thêm tên test tự động nếu có, ví dụ `AC3 · Decision Table (R1) · test_unlinked_caregiver_gets_403__AC3`; test chạy tay ghi `manual`.

ID: `TC-<MÃ>-NN`, hoặc `TC-<MÃ>-<KỸ THUẬT>-NN` (ví dụ `TC-DOSE-BVA-03`). Không đánh lại số test case đã có trong file tổng; test case bỏ đi thì xóa khỏi spec, không dùng lại số của nó.

### 3. Điền kết quả từ lần chạy thật

- Test case có test tự động đã chạy trong phiên này: lấy `actual` từ output trong `work/<task-id>/evidence/`; `status` là `Pass` hoặc `Fail`; ghi log vào `evidence` khi `Fail`.
- Test case chạy tay đã chạy trong phiên này (gọi API bằng lệnh, thao tác app): lưu output vào `evidence/testcase-<ID>.log`, rồi điền như trên.
- Chưa chạy được (cần thiết bị, cần người, cần môi trường chưa có): `status: Pending`, `actual` để trống. Liệt kê các test case này khi bàn giao để người dùng chạy và cập nhật trong file tổng.
- `Fail`: bắt buộc `severity` theo thang mức nghiêm trọng trong `AGENTS.md` (Critical, High, Medium, Low) và `root_cause` (nguyên nhân gốc đã xác định, hoặc nghi vấn kèm chữ "nghi vấn"). Script tự sinh dòng Bug Report `BUG-<MÃ>-NN` tương ứng.

### 4. Viết spec

`work/<task-id>/testcases.json`:

```json
{
  "project": "<Project Name trong AGENTS.md>",
  "functions": [
    {
      "code": "DOSE",
      "name": "Ghi nhận liều",
      "sheet": "Dose log",
      "description": "Mô tả ngắn chức năng (vào bảng Report)",
      "created_by": "<git config user.name>",
      "created_date": "YYYY-MM-DD",
      "reviewed_by": "",
      "reviewed_date": "",
      "priority": "High",
      "remarks": "Nhận xét kết quả, nguyên nhân chính của các Fail",
      "ep": [
        {"field": "client_uuid", "valid": ["UUID v4 chưa dùng"], "invalid": ["(blank)", "không phải UUID", "đã dùng"]}
      ],
      "decision_tables": [
        {"title": "Quyền xem lịch sử liều",
         "conditions": [{"name": "Có caregiver_link?", "values": ["No", "Yes", "Yes"]},
                        {"name": "Consent còn hiệu lực?", "values": ["-", "No", "Yes"]}],
         "actions": [{"name": "403 + access_logs denied", "rules": [1, 2]},
                     {"name": "200 + access_logs allowed", "rules": [3]}]}
      ],
      "cases": [
        {"id": "TC-DOSE-01", "description": "...", "precondition": "...",
         "steps": ["...", "..."], "data": "...", "expected": "...",
         "actual": "...", "status": "Pass", "comments": "AC1 · EP (1)"},
        {"id": "TC-DOSE-02", "...": "...", "status": "Fail",
         "severity": "High", "root_cause": "...", "evidence": "evidence/test-integration.log"}
      ]
    }
  ]
}
```

`sheet` tối đa 31 ký tự, không trùng sheet khác, không dùng tên `Report`. `ep` và `decision_tables` không bắt buộc nhưng phải có khi Comments tham chiếu tới chúng.

### 5. Dựng và gộp

```
python .agents/scripts/testcase_xlsx.py validate <task-id>
python .agents/scripts/testcase_xlsx.py build <task-id>
python .agents/scripts/testcase_xlsx.py merge <task-id>
```

Lưu output vào `work/<task-id>/evidence/testcase-xlsx.log`.

- `validate` báo lỗi spec: sửa spec, không lách.
- `build` ghi `work/<task-id>/testcases.xlsx` (file của riêng task).
- `merge` thay sheet cùng mã trong file tổng (`testcase-book` trong `AGENTS.md`), giữ nguyên chức năng khác, dựng lại `Report`. File tổng nằm trong submodule tài liệu: chuẩn bị nhánh theo `wf-git` trước khi chạy. Thiếu vai trò `testcase-book` thì dừng và hỏi người dùng đường dẫn file tổng.
- `CẢNH BÁO: <ID>: file đích đang là Pass/Fail, spec là ...`: file tổng có kết quả khác (thường do tester cập nhật tay). Không tự ghi đè: hỏi người dùng giữ bên nào, rồi sửa spec và chạy lại.
- File đang mở trong Excel thì script báo lỗi ghi file: nhờ người dùng đóng file.
- Thiếu `openpyxl`: báo người dùng cài (`python -m pip install openpyxl`), không tự cài vào môi trường của dự án.

### 6. Ghi vào artifact

Trong artifact của giai đoạn đang làm (`05-test-report.md`, task S thì `04-impl-notes.md`), mục "Bộ test case Excel": đường dẫn spec, file task, file tổng, số test case Pass/Fail/Pending theo chức năng, danh sách `Pending` cần người chạy, danh sách bug, đường dẫn log `evidence/testcase-xlsx.log`.

## Tự kiểm trước khi bàn giao

- [ ] Mỗi AC và mỗi kịch bản chất lượng áp dụng có ít nhất một test case; Comments ghi mã AC và kỹ thuật.
- [ ] Mỗi lớp EP và mỗi rule của bảng quyết định có test case; mỗi giới hạn có đủ bốn điểm biên.
- [ ] Mọi `Pass`/`Fail` có `actual` lấy từ lần chạy trong phiên này, truy được tới log trong `evidence/`; còn lại là `Pending`.
- [ ] Mọi `Fail` có `severity` và `root_cause`; số bug trong Report bằng số test case `Fail`.
- [ ] `validate`, `build`, `merge` đã chạy và exit 0, có log; mọi `CẢNH BÁO` đã được người dùng quyết định.
