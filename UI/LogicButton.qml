import QtQuick

Rectangle {
    id: root
    width: 22; height: 22
    radius: 6

    property string label: "A"
    property string overrideColor: "" // Nhận màu Xanh/Đỏ từ hệ thống (Câu 4)

    signal tapped()

    // Q4: xanh (FULL) / đỏ (NOT FULL). Mặc định: tối, bấm giữ -> hổ phách.
    color: overrideColor !== "" ? overrideColor : (mouseArea.pressed ? "#ff6a1a" : "#241f14")
    border.width: 2
    border.color: overrideColor !== "" ? overrideColor : "#4a3f28"
    antialiasing: true

    Text {
        anchors.centerIn: parent
        text: root.label
        color: (overrideColor !== "" || mouseArea.pressed) ? "#1a0f04" : "#e6d9b8"
        font.pixelSize: 12; font.bold: true
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: root.tapped()
    }
}
