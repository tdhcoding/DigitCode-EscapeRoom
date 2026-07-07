import QtQuick
import QtQuick.Controls

Item {
    id: root
    property bool isWin: false

    Rectangle {
        anchors.fill: parent
        color: isWin ? "#ecfdf5" : "#fef2f2"
    }

    // --- 1. TIÊU ĐỀ KHI THẮNG ---
    Text {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -90
        visible: isWin
        text: "CONGRATULATIONS!"
        font.pixelSize: 32
        font.bold: true // Tiêu đề thì in đậm
        color: "#10b981"
        font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
    }

    // --- 2. TIÊU ĐỀ KHI THUA (Xếp so le 2 dòng) ---
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -90
        visible: !isWin
        width: 320 // Giới hạn độ rộng để ép lề trái/phải
        spacing: 5

        Text {
            text: "BETTER LUCK"
            font.pixelSize: 32
            font.bold: true // Tiêu đề thì in đậm
            color: "#ef4444"
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            anchors.left: parent.left // Ép sát lề trái
        }

        Text {
            text: "NEXT LIFE..."
            font.pixelSize: 32
            font.bold: true // Tiêu đề thì in đậm
            color: "#ef4444"
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            anchors.right: parent.right // Ép sát lề phải
        }
    }

    // --- 3. CỤM NÚT ĐIỀU HƯỚNG ---
    Column {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 60
        spacing: 15

        Button {
            text: "Review Board"
            width: 180; height: 50
            font.pixelSize: 18; font.bold: false // Bỏ in đậm
            onClicked: stackView.pop()
        }

        Button {
            text: "Play Again"
            width: 180; height: 50
            font.pixelSize: 18; font.bold: false // Bỏ in đậm
            visible: isWin
            onClicked: {
                gameBoard.generateRandomPuzzle()
                stackView.pop()
            }
        }

        Button {
            text: "Main Menu"
            width: 180; height: 50
            font.pixelSize: 18; font.bold: false // Bỏ in đậm
            onClicked: stackView.pop(null)
        }
    }
}