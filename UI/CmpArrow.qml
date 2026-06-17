import QtQuick
Rectangle {
    id: root
    width: 20; height: 20
    radius: 4
    border.width: 1
    property string arrowVal: "gt"
    property bool selected: false
    property int autoVal: 0
    property bool isAuto: false
    property bool clickable: true  // ← thêm mới

    visible: !isAuto
             || (autoVal === 1 && arrowVal === "gt")
             || (autoVal === -1 && arrowVal === "lt")

    color: selected ? "#b066ff" : "#e0e0e0"
    border.color: selected ? "#9a4cee" : "#cccccc"

    signal tapped()

    Text {
        anchors.centerIn: parent
        text: root.arrowVal === "gt" ? ">" : "<"
        color: root.selected ? "#ffffff" : "#777777"
        font.pixelSize: 13
        font.bold: true
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
    }
    MouseArea {
        anchors.fill: parent
        enabled: root.clickable  // ← dùng clickable
        onClicked: {
            root.selected = !root.selected
            root.tapped()
        }
    }
}