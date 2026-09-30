---
name: wf-health-endpoint
description: Checklist bắt buộc cho mọi endpoint hay service đọc hoặc ghi dữ liệu sức khỏe — đi qua Policy Enforcement Point có sẵn, đối chiếu patient_id với liên kết người thân, không cache quyết định phân quyền, access log fail-closed, dữ liệu trả về tối thiểu, mã lỗi theo contract, đăng ký route với kiểm tra CI, và bộ test cross-patient. Use whenever a task adds or changes an endpoint or service touching medication schedules, dose logs, adherence history, medical profiles, consent, caregiver links or any patient data — e.g. "thêm endpoint lịch uống", "API lịch sử liều", "người thân xem dữ liệu", "chia sẻ", "consent" — during planning, implementation, testing or review.
---

# Endpoint dữ liệu sức khỏe

## Vai trò

Người bảo vệ dữ liệu sức khỏe.

- **Chịu trách nhiệm**: không dữ liệu sức khỏe nào đến tay người không có quyền, và mọi lần truy cập đều được ghi lại.
- **Ưu tiên khi mâu thuẫn**: từ chối sai còn hơn cho phép sai; bảo mật > tiện lợi > hiệu năng.
- **Mặc định**: mọi `patient_id` từ client là không đáng tin; lỗi khi kiểm quyền hoặc ghi log thì từ chối (fail-closed).
- **Không làm**: tự viết kiểm tra quyền riêng, cache quyết định phân quyền, log dữ liệu sức khỏe.

Skill dùng bên trong plan, implement, test, review; không có artifact riêng. Tên thành phần PEP, bảng liên kết và bảng log theo bất biến kiến trúc trong `AGENTS.md`.

## Nguyên tắc: dùng lại, không tự viết

Tìm cài đặt PEP hiện có trong backend (dependency hoặc middleware `resolve_access`, Consent Guard, Access Log Writer) và cách các endpoint hiện có dùng nó. Endpoint mới dùng đúng cơ chế đó, kể cả khi tự viết trông đơn giản hơn.

PEP chưa tồn tại trong code: dừng và báo; endpoint dữ liệu sức khỏe cần PEP làm tiền đề.

## Checklist cho plan và implement

1. **Đi qua PEP đúng thứ tự** `resolve_access → Consent Guard → Access Log Writer`, trước khi đọc hoặc ghi bất kỳ dữ liệu sức khỏe nào.
2. **Không tin `patient_id` từ client**: đối chiếu với chính người gọi (patient tự truy cập) hoặc với liên kết người thân còn hiệu lực. Áp dụng cho path, query và body.
3. **Consent theo mục đích**: xác định mục đích truy cập của endpoint, kiểm consent tương ứng và công tắc chia sẻ của patient.
4. **Không cache quyết định**: quyền đọc từ DB ở mỗi request. Không dùng claim trong JWT để phân quyền, không cache kết quả kiểm quyền ở API hay app. Rút quyền có hiệu lực ở request kế tiếp.
5. **Access log fail-closed**: truy cập được phép chỉ trả dữ liệu khi ghi log thành công; ghi log lỗi thì request lỗi. Truy cập bị từ chối ghi dòng `denied` ở transaction riêng để không bị rollback theo.
6. **Tối thiểu dữ liệu**: response chỉ chứa field mà mục đích cần; không trả nguyên bản ghi DB.
7. **Mã lỗi**: bị từ chối trả đúng mã và body mà contract quy định; nếu contract chưa quy định thì theo `AGENTS.md` (DrugTime: 403) và đưa thành câu hỏi ở giai đoạn contract. Không tự chọn 404 để "giấu" patient khi contract không nói vậy.
8. **Không log dữ liệu sức khỏe** trong log ứng dụng; chỉ định danh cần để truy vết.
9. **Đăng ký route** vào cơ chế kiểm tra enforcement mà CI dùng (danh sách route được bảo vệ, hoặc allow-list tường minh cho route công khai). Cơ chế này chưa có thì ghi vào "Phát sinh".

## Test bắt buộc

Thêm vào bộ test cross-patient (tích hợp); mỗi ca kiểm cả response lẫn access log:

| Ca | Kỳ vọng |
|---|---|
| Patient truy cập dữ liệu của chính mình | Thành công, có dòng log được phép |
| Người thân có liên kết và consent hợp lệ | Thành công, có dòng log được phép |
| Người thân không có liên kết | Bị từ chối, có dòng `denied` |
| Người thân có liên kết nhưng thiếu consent đúng mục đích | Bị từ chối, có dòng `denied` |
| Patient tắt công tắc chia sẻ | Bị từ chối, có dòng `denied` |
| Rút consent hoặc hủy liên kết, gọi lại ngay | Bị từ chối ở request kế tiếp |
| Người gọi hợp lệ nhưng sửa `patient_id` sang patient khác | Bị từ chối, có dòng `denied` |
| Ghi access log thất bại | Request thất bại, không trả dữ liệu (unit test hoặc giả lập lỗi) |

## Checklist cho review

- [ ] Endpoint dùng PEP có sẵn, không có kiểm tra quyền tự viết.
- [ ] `patient_id` ở mọi vị trí được đối chiếu.
- [ ] Không có cache hay claim phân quyền.
- [ ] Access log fail-closed; `denied` ở transaction riêng.
- [ ] Response tối thiểu; log không chứa dữ liệu sức khỏe.
- [ ] Mã lỗi khớp contract.
- [ ] Route đã đăng ký với kiểm tra CI.
- [ ] Đủ các ca trong bảng test, đã chạy và pass, có log.
