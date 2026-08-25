# Ranked Match rời khỏi Room và chỉ đến từ Matchmaking Queue

Mô hình invite-room mà [#2](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2)
và [#4](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4) xây cho phép Player
**chọn đối thủ**, và đó là điều kiện đủ để một người điều khiển hai account chuyển Elo
cho nhau. Vì mức chấp nhận rủi ro đó được chốt là **bằng không**, Ranked Match không còn
đến từ Room nữa: nó đến từ **Matchmaking Queue**, và khi không có đối thủ người thì ghép
với một **Bot Opponent** có cường độ bám theo chính Ranked Rating của người chơi — nên
rating hội tụ về trình độ thật rồi đứng lại, và leo quá trình độ thật là bất khả thi về
mặt toán học chứ không chỉ là đắt.

Quyết định đầy đủ, kèm mọi con số: **resolution comment của
[#25](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25)**. Tài liệu này cố ý
**không** chép lại nó — hai bản ghi cùng một quyết định là hai bản ghi sẽ lệch nhau.

## Vì sao không chọn đường rẻ hơn

Đã khảo sát một đòn bẩy thuần policy trước khi vẽ lại destination: **forfeit sớm thì
transfer = 0**. Nó rẻ thật — Elo không nằm trong ruleset (R-K-02 có 8 tham số
configurable, không cái nào là tham số Elo), nên không bump version, không để R-K-04 cắt
lịch sử; và `T = 0` đối xứng nên chứng minh zero-sum của #10 §1.3 còn nguyên. Nó cũng
bịt đúng chỗ: với R-T-04 và R-T-05.4, **ngoài R-T-05.3 thì mọi đường thắng đều đòi một
SOLVE thật**, nên vô hiệu giá trị Elo của forfeit sớm là xoá mọi đường thắng dưới một phút.

Nhưng nó chỉ mua được **~20×** (đường 23-donor đi từ 28 phút lên 9,2 giờ), vì kẻ tấn công
chờ hết ngưỡng hoặc chuyển sang "donor tự loại + booster Solve thật". Mọi đòn bẩy ở tầng
chính sách Elo đều tấn công **giá mỗi điểm rating**; không cái nào tấn công **quyền chọn
đối thủ**. Yêu cầu "bằng không" chỉ đạt được bằng cách bỏ quyền chọn đối thủ.

## Hệ quả không hiển nhiên

- **Room, Invite Code, Seat, Room Owner vẫn tồn tại nhưng chỉ phục vụ Practice.** Đừng
  "sửa" chỗ này: hạ tầng đó có vẻ thừa cho Ranked là **cố ý**, không phải sót.
- **Hệ thống rating là hệ lai**: người-đấu-người giữ zero-sum `+T/−T`; người-đấu-bot đổi
  rating một phía. #10 §1.3/§4.1/§4.2/§5.3 phải đọc lại với điều đó trong đầu.
- **#10 §4.1 không còn là ràng buộc lên thiết kế này.** Bài toán connected component rời
  rạc được giải **bằng cấu trúc**: mọi Player được đo bởi cùng một hàm
  `Ranked Rating → Score mục tiêu`. Cái làm rating so sánh được là cái **thước** chung,
  không phải cái **nút** chung — Bot Opponent không phải hub, nó không mang thông tin
  giữa hai người chơi.
- **Toàn bộ tính toàn vẹn của thang treo lên hàm hiệu chuẩn đó**, và hàm đó chưa tồn tại.
  Sai đơn điệu ở vùng nào thì cả vùng đó của bảng xếp hạng lệch **âm thầm**.
- **Một phần #2 và #4 mất hiệu lực** — danh sách chính xác nằm trong resolution comment
  của #25.
