import QtQuick
Rectangle {
    id: root
    width: 24; height: 20
    radius: 4
    border.width: 1
    property string dotType: "even"
    property bool selected: false
    property int autoVal: -1
    property bool clickable: true

    visible: autoVal === -1
             || (autoVal === 0 && dotType === "even")
             || (autoVal === 1 && dotType === "odd")

    color: selected ? "#b066ff" : "#e0e0e0"
    border.color: selected ? "#9a4cee" : "#cccccc"

    signal tapped()

    Text {
        anchors.centerIn: parent
        text: root.dotType === "even" ? ".." : "."
        color: root.selected ? "#ffffff" : "#777777"
        font.pixelSize: 12
        font.bold: true
        font.letterSpacing: root.dotType === "even" ? 2 : 0
    }
    MouseArea {
        anchors.fill: parent
        enabled: root.clickable  // ← dùng clickable thay vì check autoVal
        onClicked: {
            root.selected = !root.selected
            root.tapped()
        }
    }
}