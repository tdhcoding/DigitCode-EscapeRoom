import QtQuick
import QtQuick.Controls

Item {
    id: root
    objectName: "screenGame" // để Main.qml nhận diện màn hình hiện tại khi phần cứng bấm NEW GAME

    // --- BIẾN LƯU TRỮ MANH MỐI TỪ C++ ---
    property var revealedQ1: ({})
    property var revealedQ2: ({})
    property var revealedQ3: ({})
    property var revealedQ4: ({})
    property bool gameActive: false
    // Chế độ "Play in Real-life": chơi cùng phần cứng thật, không cho phép Pause
    property bool realLifeMode: false
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
        // Real-life mode: không cho Pause giữa ván (chỉ hiện lại khi ván đã kết thúc)
        visible: !root.realLifeMode || !root.gameActive

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
            // Giới hạn vùng text ở giữa: chừa khối TIME/PTS bên trái và cụm Q1-Q4
            // bên phải, tránh chữ dài chui xuống dưới nút (bug từng thấy thực tế)
            anchors.left: parent.left; anchors.leftMargin: 160
            anchors.right: parent.right; anchors.rightMargin: 215
            anchors.verticalCenter: parent.verticalCenter
            color: "#ffb700"; font.pixelSize: 15; font.bold: true
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
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

    // --- 7. CHÚ GIẢI 4 CÂU HỎI (góc dưới trái) ---
    Column {
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 12
        spacing: 2
        z: 5

        Repeater {
            model: [
                "Q1 Even/Odd  - 1 LED",
                "Q2 Compare   - 2 LEDs",
                "Q3 Count     - 1 row/col",
                "Q4 Full check- 2 rows/cols"
            ]
            delegate: Text {
                text: modelData
                font.pixelSize: 10
                color: "#6b7280"
                font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            }
        }
        Text {
            text: "-5 pts each"
            font.pixelSize: 10; font.italic: true
            color: "#9ca3af"
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
        }
    }

    // --- 8. NÚT SETTINGS (bánh răng, góc dưới phải) ---
    Button {
        id: btnSettings
        anchors.right: parent.right
        anchors.rightMargin: 15
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 15
        width: 44; height: 44; z: 10

        background: Rectangle { color: "#374151"; radius: 22 }
        contentItem: Text {
            text: "⚙" // ⚙
            color: "white"; font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        }
        onClicked: settingsPopup.open()
    }

    Popup {
        id: settingsPopup
        width: 260
        height: settingsColumn.implicitHeight + 40
        anchors.centerIn: parent
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: "#f9fafb"; radius: 10; border.color: "#d1d5db"; border.width: 2 }

        Column {
            id: settingsColumn
            anchors.centerIn: parent
            spacing: 12

            Text {
                text: "SETTINGS"
                font.pixelSize: 16; font.bold: true; color: "#374151"
                anchors.horizontalCenter: parent.horizontalCenter
                font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            }

            Button {
                text: "Rules"
                width: 200; height: 42
                anchors.horizontalCenter: parent.horizontalCenter
                background: Rectangle { color: "#ffffff"; border.color: "#ccc"; radius: 5 }
                contentItem: Text { text: parent.text; color: "black"; font.pixelSize: 15; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: { settingsPopup.close(); rulesPopup.open() }
            }

            Button {
                // Real-life mode đang chơi: không có Exit (Exit = pause trá hình)
                visible: !root.realLifeMode || !root.gameActive
                text: root.gameActive ? "Pause & Exit to Menu" : "Exit to Menu"
                width: 200; height: 42
                anchors.horizontalCenter: parent.horizontalCenter
                background: Rectangle { color: "#6b7280"; radius: 5 }
                contentItem: Text { text: parent.text; color: "white"; font.bold: true; font.pixelSize: 14; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: {
                    settingsPopup.close()
                    if (root.gameActive) {
                        gameBoard.pauseGame();
                        stackView.push("ScreenMenu.qml", { "hasSavedGame": true });
                    } else {
                        stackView.pop(null);
                    }
                }
            }

            Button {
                text: "Close"
                width: 200; height: 36
                anchors.horizontalCenter: parent.horizontalCenter
                background: Rectangle { color: "transparent"; border.color: "#d1d5db"; radius: 5 }
                contentItem: Text { text: parent.text; color: "#6b7280"; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: settingsPopup.close()
            }
        }
    }

    // --- 9. POPUP LUẬT CHƠI ---
    Popup {
        id: rulesPopup
        width: 480; height: 540
        anchors.centerIn: parent
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: "#1f2937"; radius: 10; border.color: "#4b5563"; border.width: 2 }

        Flickable {
            anchors.fill: parent
            anchors.margins: 18
            contentHeight: rulesText.implicitHeight
            clip: true

            Text {
                id: rulesText
                width: parent.width
                wrapMode: Text.WordWrap
                color: "#e5e7eb"
                font.pixelSize: 12
                font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
                lineHeight: 1.35
                text:
                    "== GOAL ==\n" +
                    "Crack the hidden 6-digit code and draw it onto the board.\n\n" +
                    "== BOARD ==\n" +
                    "6 LEDs named T U V / W X Y (2 rows x 3 cols).\n" +
                    "Buttons A-I address columns of segments, J-S address rows.\n\n" +
                    "== CLUES (-5 pts each) ==\n" +
                    "Q1 Even/Odd : pick 1 LED (T-Y), get its parity dot.\n" +
                    "Q2 Compare  : pick 2 adjacent LEDs, get < or >.\n" +
                    "Q3 Count    : pick 1 row/col (A-S), get number of lit\n" +
                    "              segments. If maxed, the group locks ON.\n" +
                    "Q4 Full     : pick 2 rows/cols, learn FULL / NOT FULL.\n" +
                    "You have 10s to pick a target after pressing Q1-Q4,\n" +
                    "or you lose 1 pt and the request is cancelled.\n\n" +
                    "== TIME & POINTS ==\n" +
                    "Start with 100 pts. Every 60s costs 1 pt.\n" +
                    "Reach 0 pts and you die.\n\n" +
                    "== REVIEW (free) ==\n" +
                    "While idle, press A-S or T-Y to re-read clues you own.\n" +
                    "Press 2 adjacent T-Y buttons to re-read their compare.\n\n" +
                    "== VERIFY (2 strikes) ==\n" +
                    "Draw all 6 digits on the board, then press VERIFY.\n" +
                    "1st wrong guess: warning. 2nd wrong guess: game over.\n\n" +
                    "== REAL-LIFE MODE ==\n" +
                    "Play with the physical board. No pause. Hold the\n" +
                    "physical NEW GAME button 5s to restart."
            }
        }

        Button {
            text: "✕"
            anchors.top: parent.top
            anchors.right: parent.right
            width: 30; height: 30
            background: Rectangle { color: "transparent" }
            contentItem: Text { text: parent.text; color: "#9ca3af"; font.pixelSize: 16; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            onClicked: rulesPopup.close()
        }
    }
}