import QtQuick

Rectangle {
    id: root
    width: 20; height: 20
    radius: 2

    property string label: "A"
    // Chế độ thường: 0=normal, 1=selected(đen), 2=crossed(đỏ)
    // Chế độ tím: 0=normal, 1=selected(tím)
    property int btnState: 0
    property bool isPurpleToggle: false // ← Thêm để phân biệt chế độ TOP và BOTTOM

    signal tapped()

    // Đổi màu nền theo chế độ màu sắc
    color: isPurpleToggle
           ? (btnState === 1 ? "#b066ff" : "#e0e0e0")
           : (btnState === 1 ? "#333333" : btnState === 2 ? "#ef4444" : "#e0e0e0")

    // Thêm viền tím khi được chọn ở chế độ TOP cho đồng bộ với Arrow/EODot
    border.width: isPurpleToggle && btnState === 1 ? 1 : 0
    border.color: "#9a4cee"

    Text {
        anchors.centerIn: parent
        text: root.label
        color: root.btnState > 0 ? "#ffffff" : "#333333"
        font.pixelSize: 12
        font.bold: true
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (root.isPurpleToggle) {
                // Chế độ TOP: Nhấn 1 lần chuyển Tím, nhấn lại về Xám (2 trạng thái)
                root.btnState = (root.btnState === 1) ? 0 : 1
            } else {
                // Chế độ BOTTOM: Giữ nguyên vòng lặp 3 trạng thái nháp
                root.btnState = (root.btnState + 1) % 3
            }
            root.tapped()
        }
    }
}