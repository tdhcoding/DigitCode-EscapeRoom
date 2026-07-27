import QtQuick
import QtQuick.Controls

// Màn chờ kết nối phần cứng cho "Play in Real-life": hiện IP server (đối chiếu
// secrets.h của firmware) + trạng thái kết nối realtime. Chỉ cho START khi ESP32 đã kết nối.
Item {
    id: root
    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : "Courier New"

    Rectangle { anchors.fill: parent; color: "#16130d" }

    Button {
        text: "❮ Back"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 140; height: 36; z: 100
        background: Rectangle { color: "#2a2416"; radius: 9; border.width: 1; border.color: "#4a3f28" }
        contentItem: Text { text: parent.text; color: "#f2ead9"; font.bold: true; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        onClicked: stackView.pop()
    }

    Column {
        anchors.centerIn: parent
        spacing: 24
        width: parent.width - 80

        Text {
            text: "PLAY IN REAL-LIFE"
            anchors.horizontalCenter: parent.horizontalCenter
            font.pixelSize: 30; font.bold: true; font.family: root.monoFont
            color: "#f2ead9"
        }

        // Bảng thông tin kết nối
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 420; height: 140
            color: "#0f0d08"; radius: 14; border.width: 1; border.color: "#5a4a28"

            Column {
                anchors.centerIn: parent
                spacing: 10

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "SERVER: " + hwServer.serverAddress
                    color: "#7fce5e"; font.pixelSize: 17; font.bold: true; font.family: root.monoFont
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "(Điền IP này vào secrets.h của firmware)"
                    color: "#9c8f72"; font.pixelSize: 11; font.family: root.monoFont
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: hwServer.connected ? "✓ THIẾT BỊ ĐÃ KẾT NỐI" : "Đang chờ thiết bị..."
                    color: hwServer.connected ? "#b7d84b" : "#ff6a1a"
                    font.pixelSize: 17; font.bold: true; font.family: root.monoFont

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
            color: "#9c8f72"; font.pixelSize: 13; font.family: root.monoFont
        }

        Button {
            text: "START"
            anchors.horizontalCenter: parent.horizontalCenter
            width: 200; height: 78
            enabled: hwServer.connected

            background: Rectangle { color: parent.enabled ? "#b7d84b" : "#3a3524"; radius: 16 }
            contentItem: Text {
                text: parent.text; color: parent.enabled ? "#12190a" : "#7a745a"; font.bold: true; font.pixelSize: 30; font.letterSpacing: 4; font.family: root.monoFont
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            }

            onClicked: {
                stackView.replace("ScreenGame.qml", { "realLifeMode": true })
                gameBoard.generateRandomPuzzle()
            }
        }
    }
}
