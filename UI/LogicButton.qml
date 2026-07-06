import QtQuick

Rectangle {
    id: root
    width: 20; height: 20
    radius: 2

    property string label: "A"
    property string overrideColor: "" // Nhận màu Xanh/Đỏ từ hệ thống (Câu 4)

    signal tapped()

    // Màu nền: Ưu tiên màu override, nếu không thì xám, khi bấm giữ thì chuyển tím
    color: overrideColor !== "" ? overrideColor : (mouseArea.pressed ? "#b066ff" : "#e0e0e0")

    Text {
        anchors.centerIn: parent
        text: root.label
        color: (overrideColor !== "" || mouseArea.pressed) ? "#ffffff" : "#333333"
        font.pixelSize: 12; font.bold: true
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: root.tapped()
    }
}