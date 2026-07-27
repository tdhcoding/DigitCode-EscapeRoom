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
    property bool realLifeMode: false
    property string oledMsg1: "Time is ticking..."
    property string oledMsg2: ""

    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : "Courier New"

    // Nền tối
    Rectangle { anchors.fill: parent; color: "#16130d" }

    // --- KẾT NỐI VỚI BACKEND (GIỮ NGUYÊN) ---
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
            verifyPopup.close()
            deniedPopup.open()
        }
    }

    // --- 1. NÚT BACK ---
    Button {
        id: btnBack
        text: root.gameActive ? "❮ Pause & Menu" : "❮ Main Menu"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 150; height: 36; z: 100
        visible: !root.realLifeMode || !root.gameActive

        background: Rectangle { color: "#2a2416"; radius: 9; border.width: 1; border.color: "#4a3f28" }
        contentItem: Text { text: parent.text; color: "#f2ead9"; font.bold: true; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }

        onClicked: {
            if (root.gameActive) {
                gameBoard.pauseGame();
                stackView.push("ScreenMenu.qml", { "hasSavedGame": true });
            } else {
                stackView.pop(null);
            }
        }
    }

    // --- 2. BẢNG OLED ĐIỀU KHIỂN (Q1-Q4 lưới 2x2) ---
    Rectangle {
        id: controlPanel
        anchors.top: btnBack.bottom
        anchors.topMargin: 16
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 15
        anchors.rightMargin: 15
        height: 84
        color: "#0f0d08"; radius: 14; border.width: 1; border.color: "#5a4a28"

        Text {
            anchors.left: parent.left; anchors.leftMargin: 20; anchors.verticalCenter: parent.verticalCenter
            color: "#7fce5e"; font.pixelSize: 15; font.bold: true; font.family: root.monoFont
            text: {
                let m = Math.floor(gameBoard.playTimeSeconds / 60)
                let s = gameBoard.playTimeSeconds % 60
                return "TIME: " + (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s + "\nPTS : " + gameBoard.points
            }
        }

        Text {
            anchors.left: parent.left; anchors.leftMargin: 170
            anchors.right: parent.right; anchors.rightMargin: 130
            anchors.verticalCenter: parent.verticalCenter
            color: "#b7d84b"; font.pixelSize: 15; font.bold: true; font.family: root.monoFont
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: root.oledMsg1 + (root.oledMsg2 !== "" ? "\n" + root.oledMsg2 : "")
        }

        Grid {
            anchors.right: parent.right; anchors.rightMargin: 18; anchors.verticalCenter: parent.verticalCenter
            columns: 2; rowSpacing: 8; columnSpacing: 8
            Repeater {
                model: ["Q1", "Q2", "Q3", "Q4"]
                delegate: Rectangle {
                    required property string modelData
                    width: 44; height: 30; color: "#ff6a1a"; radius: 8; border.width: 1; border.color: "#ff8a44"
                    Text { anchors.centerIn: parent; text: modelData; color: "#1a0f04"; font.bold: true; font.pixelSize: 13; font.family: root.monoFont }
                    MouseArea { anchors.fill: parent; onClicked: gameBoard.handleButtonPress("SW", "BTN_" + modelData) }
                }
            }
        }
    }

    // --- 3. SA BÀN ---
    BottomBoard {
        anchors.top: controlPanel.bottom
        anchors.topMargin: 12
        anchors.bottom: btnVerify.top
        anchors.bottomMargin: 8
        anchors.left: parent.left
        anchors.right: parent.right

        revealedQ1: root.revealedQ1
        revealedQ2: root.revealedQ2
        revealedQ3: root.revealedQ3
        revealedQ4: root.revealedQ4
        gameActive: root.gameActive
    }

    // --- 4. NÚT VERIFY ---
    Button {
        id: btnVerify
        text: "VERIFY"
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        anchors.horizontalCenter: parent.horizontalCenter
        width: 190; height: 52; z: 10
        visible: root.gameActive

        background: Rectangle { color: "#ff6a1a"; radius: 12; border.width: 1; border.color: "#ff8a44" }
        contentItem: Text {
            text: parent.text; color: "#1a0f04"; font.bold: true; font.pixelSize: 21
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            font.family: root.monoFont
        }

        onClicked: { verifyPopup.open(); txtCodeInput.forceActiveFocus() }
    }

    // --- 5. POPUP NHẬP MÃ 6 SỐ ---
    Popup {
        id: verifyPopup
        width: 320; height: 200
        anchors.centerIn: parent
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: "#1c1810"; radius: 14; border.color: "#5a4a28"; border.width: 2 }

        Column {
            anchors.centerIn: parent
            spacing: 20
            Text {
                text: "ENTER 6 DIGITS CODE"
                font.pixelSize: 18; font.bold: true; color: "#f2ead9"
                anchors.horizontalCenter: parent.horizontalCenter
                font.family: root.monoFont
            }
            TextField {
                id: txtCodeInput
                width: 240; height: 50
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 24; font.letterSpacing: 8; font.bold: true
                horizontalAlignment: TextInput.AlignHCenter
                inputMethodHints: Qt.ImhDigitsOnly
                maximumLength: 6
                color: "#ffb000"
                background: Rectangle { color: "#0c0a05"; radius: 8; border.color: "#5a4a28"; border.width: 2 }
                validator: RegularExpressionValidator { regularExpression: /^[0-9]{0,6}$/ }
                onVisibleChanged: { if (!visible) text = "" }
            }
            Button {
                text: "ACCESS"
                width: 150; height: 45
                anchors.horizontalCenter: parent.horizontalCenter
                enabled: txtCodeInput.text.length === 6
                background: Rectangle { color: parent.enabled ? "#b7d84b" : "#3a3524"; radius: 10 }
                contentItem: Text { text: parent.text; color: parent.enabled ? "#12190a" : "#7a745a"; font.bold: true; font.pixelSize: 18; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: gameBoard.verifyCode(txtCodeInput.text)
            }
        }
    }

    // --- 6. POPUP CẢNH BÁO SAI MÃ LẦN 1 ---
    Popup {
        id: deniedPopup
        anchors.centerIn: parent
        width: root.width; height: root.height
        modal: true; focus: true
        closePolicy: Popup.NoAutoClose
        background: Rectangle { color: Qt.rgba(0, 0, 0, 0.8) }

        Rectangle {
            anchors.centerIn: parent
            width: 420; height: 130
            color: "transparent"; border.color: "#ef4444"; border.width: 4; radius: 10
            Text {
                anchors.centerIn: parent
                text: "ACCESS DENIED\nYOU HAVE ONE LAST CHANCE"
                color: "#ef4444"; font.pixelSize: 22; font.bold: true
                horizontalAlignment: Text.AlignHCenter
                font.family: root.monoFont; lineHeight: 1.5
            }
            SequentialAnimation on border.color {
                loops: Animation.Infinite
                ColorAnimation { from: "#ef4444"; to: "transparent"; duration: 300 }
                ColorAnimation { from: "transparent"; to: "#ef4444"; duration: 300 }
            }
        }
        Timer { id: closeDeniedTimer; interval: 4000; onTriggered: deniedPopup.close() }
        onOpened: closeDeniedTimer.start()
        onClosed: closeDeniedTimer.stop()
    }

    // --- 7. CHÚ GIẢI 4 CÂU HỎI ---
    Column {
        anchors.left: parent.left
        anchors.leftMargin: 15
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 14
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
                required property string modelData
                text: modelData; font.pixelSize: 10; color: "#9c8f72"; font.family: root.monoFont
            }
        }
        Text { text: "-5 pts each"; font.pixelSize: 10; font.italic: true; color: "#7a745a"; font.family: root.monoFont }
    }

    // --- 8. NÚT SETTINGS ---
    Button {
        id: btnSettings
        anchors.right: parent.right
        anchors.rightMargin: 15
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        width: 44; height: 44; z: 10
        background: Rectangle { color: "#2a2416"; radius: 22; border.width: 1; border.color: "#4a3f28" }
        contentItem: Text { text: "⚙"; color: "#f2ead9"; font.pixelSize: 24; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        onClicked: settingsPopup.open()
    }

    Popup {
        id: settingsPopup
        width: 260
        height: settingsColumn.implicitHeight + 40
        anchors.centerIn: parent
        modal: true; focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { color: "#1c1810"; radius: 14; border.color: "#5a4a28"; border.width: 2 }

        Column {
            id: settingsColumn
            anchors.centerIn: parent
            spacing: 12
            Text {
                text: "SETTINGS"; font.pixelSize: 16; font.bold: true; color: "#f2ead9"
                anchors.horizontalCenter: parent.horizontalCenter; font.family: root.monoFont
            }
            Button {
                text: "Rules"
                width: 200; height: 42
                anchors.horizontalCenter: parent.horizontalCenter
                background: Rectangle { color: "#241f14"; border.color: "#4a3f28"; border.width: 1; radius: 8 }
                contentItem: Text { text: parent.text; color: "#f2ead9"; font.pixelSize: 15; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                onClicked: { settingsPopup.close(); rulesPopup.open() }
            }
            Button {
                visible: !root.realLifeMode || !root.gameActive
                text: root.gameActive ? "Pause & Exit to Menu" : "Exit to Menu"
                width: 200; height: 42
                anchors.horizontalCenter: parent.horizontalCenter
                background: Rectangle { color: "#2a2416"; radius: 8; border.width: 1; border.color: "#4a3f28" }
                contentItem: Text { text: parent.text; color: "#f2ead9"; font.bold: true; font.pixelSize: 14; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
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
                background: Rectangle { color: "transparent"; border.color: "#4a3f28"; border.width: 1; radius: 8 }
                contentItem: Text { text: parent.text; color: "#9c8f72"; font.pixelSize: 13; font.family: root.monoFont; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
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
        background: Rectangle { color: "#14110b"; radius: 14; border.color: "#5a4a28"; border.width: 2 }

        Flickable {
            anchors.fill: parent
            anchors.margins: 18
            contentHeight: rulesText.implicitHeight
            clip: true
            Text {
                id: rulesText
                width: parent.width
                wrapMode: Text.WordWrap
                color: "#e6d9b8"
                font.pixelSize: 12
                font.family: root.monoFont
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
            contentItem: Text { text: parent.text; color: "#9c8f72"; font.pixelSize: 16; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            onClicked: rulesPopup.close()
        }
    }
}
