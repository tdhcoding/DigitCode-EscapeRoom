import QtQuick
import QtQuick.Controls

// Màn hình chờ kết nối phần cứng cho chế độ "Play in Real-life":
// hiển thị IP server (để đối chiếu secrets.h của firmware) và trạng thái
// kết nối theo thời gian thực. Chỉ cho START khi ESP32 đã kết nối.
// Trong chế độ này game KHÔNG cho phép Pause (xem ScreenGame.realLifeMode).
Item {
    id: root

    Rectangle {
        anchors.fill: parent
        color: "#e5e7eb"
    }

    Button {
        text: "❮ Back"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 140; height: 35; z: 100
        background: Rectangle { color: "#6b7280"; radius: 5 }
        contentItem: Text { text: parent.text; color: "white"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        onClicked: stackView.pop()
    }

    Column {
        anchors.centerIn: parent
        spacing: 24
        width: parent.width - 80

        Text {
            text: "PLAY IN REAL-LIFE"
            anchors.horizontalCenter: parent.horizontalCenter
            font.pixelSize: 30; font.bold: true
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            color: "#111827"
        }

        // Bảng thông tin kết nối
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 400; height: 130
            color: "#2d2d2d"; radius: 8

            Column {
                anchors.centerIn: parent
                spacing: 10

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "SERVER: " + hwServer.serverAddress
                    color: "#10b981"; font.pixelSize: 16; font.bold: true
                    font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "(Điền IP này vào secrets.h của firmware)"
                    color: "#9ca3af"; font.pixelSize: 11
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: hwServer.connected ? "✓ THIẾT BỊ ĐÃ KẾT NỐI" : "Đang chờ thiết bị..."
                    color: hwServer.connected ? "#10b981" : "#ffb700"
                    font.pixelSize: 17; font.bold: true
                    font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"

                    // Nhấp nháy nhẹ khi đang chờ
                    SequentialAnimation on opacity {
                        running: !hwServer.connected
                        loops: Animation.Infinite
                        NumberAnimation { from: 1.0; to: 0.3; duration: 700 }
                        NumberAnimation { from: 0.3; to: 1.0; duration: 700 }
                    }
                    onTextChanged: opacity = 1.0
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Chế độ chơi cùng sa bàn thật — không thể Pause giữa ván."
            color: "#6b7280"; font.pixelSize: 13
        }

        Button {
            text: "START"
            anchors.horizontalCenter: parent.horizontalCenter
            width: 180; height: 70
            font.pixelSize: 24; font.bold: true
            enabled: hwServer.connected

            background: Rectangle { color: parent.enabled ? "#10b981" : "#9ca3af"; radius: 6 }
            contentItem: Text {
                text: parent.text; color: "white"; font.bold: true; font.pixelSize: 24
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }

            onClicked: {
                // Giống luồng READY: điều hướng TRƯỚC rồi mới sinh đề, để màn hình
                // game kịp nhận tín hiệu puzzleGenerated
                stackView.replace("ScreenGame.qml", { "realLifeMode": true })
                gameBoard.generateRandomPuzzle()
            }
        }
    }
}
