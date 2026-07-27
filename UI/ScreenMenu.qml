import QtQuick
import QtQuick.Controls

Item {
    id: root

    // Cờ hiệu: true nếu màn này bật lên từ "Back to Menu"
    property bool hasSavedGame: false
    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : "Courier New"

    Rectangle { anchors.fill: parent; color: "#16130d" }

    // Nút menu tông tối, tái sử dụng
    component MenuBtn: Button {
        id: ctrl
        property color bg: "#241f14"
        property color fg: "#f2ead9"
        property color bord: "#4a3f28"
        property bool primary: false
        width: 250; height: 56
        background: Rectangle { color: ctrl.enabled ? ctrl.bg : "#1a160e"; radius: 12; border.width: ctrl.primary ? 0 : 2; border.color: ctrl.bord }
        contentItem: Text {
            text: ctrl.text; color: ctrl.enabled ? ctrl.fg : "#6b6350"
            font.pixelSize: 17; font.bold: ctrl.primary; font.family: root.monoFont
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: 18

        // --- Thương hiệu ---
        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 10
            bottomPadding: 14
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "CYBER-PHYSICAL ESCAPE ROOM"
                color: "#9c8f72"; font.pixelSize: 12; font.letterSpacing: 4; font.family: root.monoFont
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                Text { text: "DIGIT"; color: "#f2ead9"; font.pixelSize: 46; font.bold: true; font.family: root.monoFont }
                Text { text: "_";     color: "#ff6a1a"; font.pixelSize: 46; font.bold: true; font.family: root.monoFont }
                Text { text: "CODE";  color: "#f2ead9"; font.pixelSize: 46; font.bold: true; font.family: root.monoFont }
            }
        }

        // 1. CONTINUE (chỉ khi có game tạm dừng)
        MenuBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: root.hasSavedGame
            text: "Continue"
            primary: true; bg: "#b7d84b"; fg: "#12190a"
            onClicked: { gameBoard.resumeGame(); stackView.pop() }
        }

        // 2. CHƠI MỚI
        MenuBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.hasSavedGame ? "New Single Challenge" : "Single Challenge"
            primary: true
            bg: root.hasSavedGame ? "#e5484d" : "#ff6a1a"
            fg: root.hasSavedGame ? "#ffffff" : "#1a0f04"
            onClicked: {
                if (root.hasSavedGame) { stackView.pop(null); stackView.push("ScreenReady.qml") }
                else { stackView.push("ScreenReady.qml") }
            }
        }

        // 3. CHƠI VỚI PHẦN CỨNG THẬT
        MenuBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Play in Real-life"
            primary: hwServer.connected
            bg: hwServer.connected ? "#b7d84b" : "#241f14"
            fg: hwServer.connected ? "#12190a" : "#f2ead9"
            onClicked: {
                if (root.hasSavedGame) { stackView.pop(null) }
                stackView.push("ScreenRealLife.qml")
            }
        }

        // 4. 1v1 (khoá)
        MenuBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "1v1 Challenge"
            enabled: false
        }

        // 5. RULES
        MenuBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Rules"
        }
    }

    Text {
        anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 18
        text: "v6 · SINGLE"; color: "#6b6350"; font.pixelSize: 12; font.family: root.monoFont
    }
}
