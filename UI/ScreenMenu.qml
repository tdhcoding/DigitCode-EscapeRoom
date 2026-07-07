import QtQuick
import QtQuick.Controls

Item {
    id: root

    // Biến cờ hiệu: true nếu màn hình này được bật lên từ nút "Back to Menu"
    property bool hasSavedGame: false

    Rectangle {
        anchors.fill: parent
        color: "#f3f4f6"
    }

    Text {
        anchors.top: parent.top
        anchors.topMargin: 80
        anchors.horizontalCenter: parent.horizontalCenter
        text: "DIGIT_CODE"
        font.pixelSize: 45
        font.bold: true
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
    }

    Column {
        anchors.centerIn: parent
        spacing: 20

        // 1. NÚT CONTINUE (Chỉ hiện khi có game đang tạm dừng)
        Button {
            text: "Continue"
            width: 220; height: 55
            font.pixelSize: 18
            visible: root.hasSavedGame // Ẩn/hiện dựa vào cờ hiệu

            background: Rectangle { color: "#10b981"; radius: 5 } // Màu xanh lá nổi bật
            contentItem: Text { text: parent.text; color: "white"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }

            onClicked: {
                gameBoard.resumeGame(); // Đánh thức Timer chạy lại
                stackView.pop(); // Rút Menu này ra khỏi ngăn xếp -> Lộ ra ScreenGame nguyên vẹn ở bên dưới!
            }
        }

        // 2. NÚT CHƠI MỚI
        Button {
            text: root.hasSavedGame ? "New Single Challenge" : "Single Challenge"
            width: 220; height: 55
            font.pixelSize: 18

            background: Rectangle { color: root.hasSavedGame ? "#ef4444" : "#ffffff"; border.color: "#ccc"; radius: 5 }
            contentItem: Text {
                text: parent.text; color: root.hasSavedGame ? "white" : "black";
                font.bold: false; font.pixelSize: 18;
                horizontalAlignment: Text.AlignHCenter;
                verticalAlignment: Text.AlignVCenter
            }

            onClicked: {
                if (root.hasSavedGame) {
                    // Nếu đang có game cũ mà vẫn bấm chơi mới -> Phá hủy toàn bộ ngăn xếp về tận gốc
                    stackView.pop(null);
                    stackView.push("ScreenReady.qml"); // Sau đó mở màn hình Ready
                } else {
                    stackView.push("ScreenReady.qml");
                }
            }
        }

        Button {
            text: "1v1 Challenge"
            width: 220; height: 55
            font.pixelSize: 18
            enabled: false
        }

        Button {
            text: "Rules"
            width: 220; height: 55
            font.pixelSize: 18
        }
    }
}