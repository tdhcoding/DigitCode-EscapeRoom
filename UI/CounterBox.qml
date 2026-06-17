import QtQuick

Rectangle {
    id: root
    width: 28; height: 26
    border.color: "#777777"
    border.width: 1
    color: "#ffffff"
    radius: 0

    property int maxVal: 6
    property int value: -1  // -1 = trống

    Text {
        anchors.centerIn: parent
        text: root.value >= 0 ? root.value : ""
        font.pixelSize: 14
        font.bold: true
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
        color: "#333333"
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (root.value < 0) root.value = 0
            else if (root.value >= root.maxVal) root.value = -1
            else root.value++
        }
    }
}