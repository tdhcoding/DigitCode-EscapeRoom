# 📂 CẤU TRÚC THƯ MỤC & CHỨC NĂNG FILE (DIGITCODE v5.0)

```text
DigitCode_SINGLE/
├── CMakeLists.txt              # Cấu hình biên dịch Qt6 (Core, Gui, Qml, Quick, WebSockets)
├── main.cpp                    # Entry point: Set QT_QUICK_CONTROLS_STYLE, khởi tạo QML & Server
├── backend/
│   ├── gameboard.h             # Header: Khai báo State Machine, Q_PROPERTY, Q_INVOKABLE, Signals
│   ├── gameboard.cpp           # Logic: Thuật toán Sudoku, Timer 60s/10s, chấm điểm, kiểm tra 2-Strike
│   ├── hardwareserver.h        # Header: Khai báo QWebSocketServer, danh sách Client ESP32
│   └── hardwareserver.cpp      # Network: Lắng nghe port 8080, parse JSON gửi/nhận với ESP32
└── UI/
    ├── Main.qml                # Bộ khung ApplicationWindow & StackView điều hướng chính
    ├── ScreenMenu.qml          # Màn hình Menu (Nút Single Challenge, Continue, Rules)
    ├── ScreenReady.qml         # Màn hình chuẩn bị (Nút READY kích hoạt tạo đề mới)
    ├── ScreenGame.qml          # Màn hình game: Chứa OLED ảo, Nút VERIFY, Popup 2-Strike, Nút Pause
    ├── ScreenResult.qml        # Màn hình Win/Lose: Tiêu đề so le, Nút Review Board, Play Again
    ├── BottomBoard.qml         # Sa bàn LED: Tích hợp Auto-Scale Container, chứa lưới nút A-S, T-Y
    ├── LedDisplay.qml          # Component: Render 7 vạch LED bằng QML Shapes (HSegment/VSegment)
    ├── LogicButton.qml         # Component: Nút bấm A-S, T-Y (Đổi màu theo trạng thái Q4 đỏ/xanh)
    ├── CounterBox.qml          # Component: Ô hiển thị số lượng quỷ đếm được từ Q3
    ├── EODot.qml               # Component: Chấm Chẵn/Lẻ (Tàng hình cho đến khi có dữ liệu từ Q1)
    └── CmpArrow.qml            # Component: Mũi tên so sánh lớn/bé (Tàng hình cho đến khi mua Q2)