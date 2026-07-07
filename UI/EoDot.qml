import QtQuick
Rectangle {
    id: root
    width: 24; height: 20
    radius: 4
    border.width: 1

    // Thêm property để nhận giá trị từ hệ thống (truyền từ LedDisplay)
    property int systemValue: -1
    property string dotType: "even"

    // CHỈ HIỆN KHI systemValue khác -1 (tức là đã được hệ thống trả về)
    visible: systemValue !== -1

    color: "#b066ff"
    border.color: "#9a4cee"

    Text {
        anchors.centerIn: parent
        text: root.dotType === "even" ? ".." : "."
        color: "#fff"
        font.pixelSize: 12
        font.bold: true
        font.letterSpacing: root.dotType === "even" ? 2 : 0
    }
}