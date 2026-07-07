import QtQuick
import QtQuick.Controls

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
        background: Rectangle {
            color: "#6b7280"
            radius: 5
        }
        contentItem: Text { text: parent.text; color: "white"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }

        onClicked: stackView.pop() // Quay về màn trước đó
    }

    Button {
        text: "READY"
        anchors.centerIn: parent
        width: 180; height: 70
        font.pixelSize: 24
        font.bold: true
        onClicked: {
            stackView.replace("ScreenGame.qml") // Dùng replace để vứt màn Ready đi, không cho quay lại

            gameBoard.generateRandomPuzzle()
        }
    }
}