import QtQuick
import QtQuick.Controls

Item {
    id: root
    property bool isWin: false
    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : "Courier New"

    Rectangle { anchors.fill: parent; color: "#16130d" }

    component ResBtn: Button {
        id: ctrl
        property bool primary: false
        width: 200; height: 50
        background: Rectangle { color: ctrl.primary ? "#ff6a1a" : "#241f14"; radius: 11; border.width: ctrl.primary ? 0 : 2; border.color: "#4a3f28" }
        contentItem: Text { text: ctrl.text; color: ctrl.primary ? "#1a0f04" : "#f2ead9"; font.pixelSize: 17; font.bold: ctrl.primary; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    }

    // --- Tiêu đề THẮNG ---
    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -96
        visible: root.isWin
        text: "CONGRATULATIONS!"
        font.pixelSize: 34; font.bold: true; color: "#b7d84b"
        font.family: root.monoFont
    }

    // --- Tiêu đề THUA (so le) ---
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -100
        visible: !root.isWin
        width: 340
        spacing: 4
        Text { text: "BETTER LUCK"; font.pixelSize: 34; font.bold: true; color: "#e5484d"; font.family: root.monoFont; anchors.left: parent.left }
        Text { text: "NEXT LIFE..."; font.pixelSize: 34; font.bold: true; color: "#e5484d"; font.family: root.monoFont; anchors.right: parent.right }
    }

    // --- Cụm nút ---
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 56
        spacing: 15

        ResBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Review Board"
            onClicked: stackView.pop()
        }
        ResBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Play Again"
            primary: true
            visible: root.isWin
            onClicked: { gameBoard.generateRandomPuzzle(); stackView.pop() }
        }
        ResBtn {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Main Menu"
            onClicked: stackView.pop(null)
        }
    }
}
