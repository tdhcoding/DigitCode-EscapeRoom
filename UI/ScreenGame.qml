import QtQuick
import QtQuick.Controls

Item {
    id: root

    // --- BIẾN LƯU TRỮ MANH MỐI TỪ C++ ---
    property var revealedQ1: ({})
    property var revealedQ2: ({})
    property var revealedQ3: ({})
    property var revealedQ4: ({})
    property bool gameActive: false
    property string oledMsg1: "Time is ticking..."
    property string oledMsg2: ""

    // --- KẾT NỐI VỚI BACKEND ---
    Connections {
        target: gameBoard

        function onGameWon() { root.gameActive = false; stackView.push("ScreenResult.qml", { "isWin": true }) }
        function onGameLost() { root.gameActive = false; stackView.push("ScreenResult.qml", { "isWin": false }) }

        function onPuzzleGenerated() {
            root.revealedQ1 = ({}); root.revealedQ2 = ({}); root.revealedQ3 = ({}); root.revealedQ4 = ({})
            root.gameActive = true
            root.oledMsg1 = "Time is ticking..."; root.oledMsg2 = ""
        }

        function onClueRevealed(clueType, targetId, value) {
            if (clueType === "Q1_EODOT") { let temp = root.revealedQ1; temp[targetId] = value; root.revealedQ1 = Object.assign({}, temp) }
            else if (clueType === "Q2_ARROW") { let temp = root.revealedQ2; temp[targetId] = value; root.revealedQ2 = Object.assign({}, temp) }
            else if (clueType === "Q3_COUNTER") { let temp = root.revealedQ3; temp[targetId] = value; root.revealedQ3 = Object.assign({}, temp) }
            else if (clueType === "Q4_FULL") { let temp = root.revealedQ4; temp[targetId] = value; root.revealedQ4 = Object.assign({}, temp) }
        }

        function onOledUpdateRequested(line1, line2) {
            if (line2 === "DEFAULT_LAYOUT" || line1.includes("[mm:ss]")) {
                root.oledMsg1 = "Time is ticking..."; root.oledMsg2 = ""
            } else { root.oledMsg1 = line1; root.oledMsg2 = line2 }
        }

        function onWrongGuessWarning() {
                    verifyPopup.close() // Đóng hộp nhập liệu
                    deniedPopup.open()  // Mở màn hình cảnh báo nhấp nháy đỏ
                }
    }

    // --- 1. NÚT BACK ---
    Button {
        id: btnBack
        // Đổi tên nút tùy theo trạng thái đang chơi hay đang review
        text: root.gameActive ? "❮ Pause & Menu" : "❮ Main Menu"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 140; height: 35; z: 100

        background: Rectangle {
            color: root.gameActive ? "#6b7280" : "#374151" // Khi review nút sẽ có màu tối hơn
            radius: 5
        }
        contentItem: Text { text: parent.text; color: "white"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }

        onClicked: {
            if (root.gameActive) {
                // Đang chơi dở -> Đóng băng và hiện nút Continue ở Menu
                gameBoard.pauseGame();
                stackView.push("ScreenMenu.qml", { "hasSavedGame": true });
            } else {
                // Đang Review (Game Over) -> Về thẳng Menu và xóa sạch ngăn xếp
                stackView.pop(null);
            }
        }
    }

    // --- 2. BẢNG OLED ĐIỀU KHIỂN ---
    Rectangle {
        id: controlPanel
        // Kéo mảng OLED xuống dưới nút Back
        anchors.top: btnBack.bottom
        anchors.topMargin: 20
        // Kéo giãn full ngang màn hình (chừa lề 15px cho đẹp)
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 15
        anchors.rightMargin: 15
        height: 70
        color: "#2d2d2d"; radius: 8

        Text {
            anchors.left: parent.left; anchors.leftMargin: 20; anchors.verticalCenter: parent.verticalCenter
            color: "#10b981"; font.pixelSize: 14; font.bold: true; font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            text: {
                let m = Math.floor(gameBoard.playTimeSeconds / 60)
                let s = gameBoard.playTimeSeconds % 60
                return "TIME: " + (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s + "\nPTS : " + gameBoard.points
            }
        }

        Text {
            anchors.centerIn: parent; color: "#ffb700"; font.pixelSize: 15; font.bold: true
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"; horizontalAlignment: Text.AlignHCenter
            text: root.oledMsg1 + (root.oledMsg2 !== "" ? "\n" + root.oledMsg2 : "")
        }

        Row {
            anchors.right: parent.right; anchors.rightMargin: 20; anchors.verticalCenter: parent.verticalCenter; spacing: 8
            Repeater {
                model: ["Q1", "Q2", "Q3", "Q4"]
                delegate: Rectangle {
                    width: 38; height: 32; color: "#b066ff"; radius: 6
                    Text { anchors.centerIn: parent; text: modelData; color: "white"; font.bold: true; font.pixelSize: 13 }
                    MouseArea { anchors.fill: parent; onClicked: gameBoard.handleButtonPress("SW", "BTN_" + modelData) }
                }
            }
        }
    }

    // --- 3. GỌI SA BÀN VÀ TRUYỀN DỮ LIỆU XUỐNG ---
    BottomBoard {
        anchors.top: controlPanel.bottom
        anchors.topMargin: 15

        anchors.bottom: btnVerify.top
        anchors.bottomMargin: 10

        anchors.left: parent.left
        anchors.right: parent.right

        revealedQ1: root.revealedQ1
        revealedQ2: root.revealedQ2
        revealedQ3: root.revealedQ3
        revealedQ4: root.revealedQ4
        gameActive: root.gameActive
    }

    // --- 4. NÚT VERIFY (NẰM DƯỚI CÙNG) ---
    Button {
        id: btnVerify
        text: "VERIFY"
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 15
        anchors.horizontalCenter: parent.horizontalCenter
        width: 180; height: 50; z: 10
        visible: root.gameActive

        background: Rectangle { color: "#ffb700"; radius: 6 }
        contentItem: Text {
            text: parent.text; color: "#111"; font.bold: true; font.pixelSize: 20
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
        }

        onClicked: {
            verifyPopup.open()
            txtCodeInput.forceActiveFocus() // Tự động trỏ nháy chuột vào ô nhập
        }
    }

    // --- 5. POPUP NHẬP MÃ 6 SỐ ---
    Popup {
        id: verifyPopup
        width: 320; height: 200
        anchors.centerIn: parent
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle { color: "#f9fafb"; radius: 10; border.color: "#d1d5db"; border.width: 2 }

        Column {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "ENTER 6 DIGITS CODE"
                font.pixelSize: 18; font.bold: true; color: "#374151"
                anchors.horizontalCenter: parent.horizontalCenter
                font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            }

            TextField {
                id: txtCodeInput
                width: 240; height: 50
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 24; font.letterSpacing: 8; font.bold: true
                horizontalAlignment: TextInput.AlignHCenter
                inputMethodHints: Qt.ImhDigitsOnly
                maximumLength: 6
                color: "#111"

                // Chỉ cho phép nhập đúng số từ 0-9
                validator: RegularExpressionValidator { regularExpression: /^[0-9]{0,6}$/ }

                // Tự động xóa trắng mỗi khi bật popup lên
                onVisibleChanged: { if (!visible) text = "" }
            }

            Button {
                text: "ACCESS"
                width: 150; height: 45
                anchors.horizontalCenter: parent.horizontalCenter
                // Nút chỉ sáng lên khi đã nhập đủ 6 số
                enabled: txtCodeInput.text.length === 6

                background: Rectangle { color: parent.enabled ? "#10b981" : "#9ca3af"; radius: 5 }
                contentItem: Text { text: parent.text; color: "white"; font.bold: true; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }

                onClicked: {
                    gameBoard.verifyCode(txtCodeInput.text)
                }
            }
        }
    }

    // --- 6. POPUP CẢNH BÁO SAI MÃ LẦN 1 ---
    Popup {
        id: deniedPopup
        anchors.centerIn: parent
        width: root.width; height: root.height // Che phủ toàn bộ màn hình
        modal: true; focus: true
        closePolicy: Popup.NoAutoClose // Khóa cứng, không cho bấm ra ngoài để tắt

        background: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) } // Làm nền tối mờ đi 80%

        Rectangle {
            anchors.centerIn: parent
            width: 420; height: 130
            color: "transparent"
            border.color: "#ef4444"
            border.width: 4
            radius: 8

            Text {
                anchors.centerIn: parent
                text: "ACCESS DENIED\nYOU HAVE ONE LAST CHANCE"
                color: "#ef4444"
                font.pixelSize: 22
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
                lineHeight: 1.5
            }

            // Hiệu ứng viền nhấp nháy Đỏ - Trong suốt (chu kỳ 0.3s)
            SequentialAnimation on border.color {
                loops: Animation.Infinite
                ColorAnimation { from: "#ef4444"; to: "transparent"; duration: 300 }
                ColorAnimation { from: "transparent"; to: "#ef4444"; duration: 300 }
            }
        }

        // Đồng hồ đếm 4s để tự động tắt Popup
        Timer {
            id: closeDeniedTimer
            interval: 4000
            onTriggered: deniedPopup.close()
        }

        onOpened: closeDeniedTimer.start()
        onClosed: closeDeniedTimer.stop()
    }
}