import QtQuick
import QtQuick.Controls

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
        spacing: 26

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "SINGLE CHALLENGE"
            color: "#ff6a1a"; font.pixelSize: 16; font.letterSpacing: 6; font.bold: true; font.family: root.monoFont
        }

        Button {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "READY"
            width: 200; height: 78
            background: Rectangle { color: "#ff6a1a"; radius: 16; border.width: 1; border.color: "#ff8a44" }
            contentItem: Text { text: parent.text; color: "#1a0f04"; font.bold: true; font.pixelSize: 30; font.letterSpacing: 4; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            onClicked: {
                stackView.replace("ScreenGame.qml")
                gameBoard.generateRandomPuzzle()
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 360
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: "Bắt đầu với 100 điểm. Đồng hồ chạy ngay khi vào — mỗi 60s trừ 1 điểm."
            color: "#9c8f72"; font.pixelSize: 13; font.family: root.monoFont
        }
    }
}
