# Triage Labels

Mọi issue đã triage mang **đúng một nhãn phân loại** và **đúng một nhãn trạng thái**.
Hai trục độc lập nhau: phân loại nói issue *là gì*, trạng thái nói nó *đang chờ ai*.

Nhãn dưới đây là nhãn có thật trong `tdhcoding/DigitCode-EscapeRoom`.
Kiểm chứng: `gh label list`

## Trục phân loại

| Nhãn | Nghĩa |
| --- | --- |
| `bug` | Có thứ đang hỏng |
| `enhancement` | Tính năng mới hoặc cải tiến |
| `documentation` | Chỉ động tới tài liệu |

## Trục trạng thái

| Nhãn | Nghĩa |
| --- | --- |
| `needs-triage` | Chưa phân loại — cần người đánh giá |
| `needs-info` | Đang chờ thêm thông tin từ người báo |
| `ready-for-agent` | Đã đặc tả đủ, agent chạy AFK được |
| `ready-for-human` | Cần người tự làm, không giao agent |
| `wontfix` | Sẽ không xử lý |

Khi một skill nhắc tới vai trò (ví dụ "apply the AFK-ready triage label"),
dùng chuỗi nhãn tương ứng ở bảng trên.

## Thêm nhãn mới

Tạo trên GitHub trước, rồi mới thêm dòng vào đây — file này mô tả tracker,
không định nghĩa nó:

```sh
gh label create <tên> --color <hex> --description "..."
```
