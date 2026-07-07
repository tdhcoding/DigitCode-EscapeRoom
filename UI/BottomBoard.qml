import QtQuick
import QtQuick.Controls

Item {
    id: root

    // Nhận dữ liệu từ ScreenGame truyền xuống
    property var revealedQ1: ({})
    property var revealedQ2: ({})
    property var revealedQ3: ({})
    property var revealedQ4: ({})
    property bool gameActive: false

    readonly property var rowBtn1Names: ["J","K","L","M","N"]
    readonly property var rowBtn2Names: ["O","P","Q","R","S"]
    readonly property var rowBtnY: [-7, 15, 36, 57, 79]

    function evenOdd(i) { let id = ["T","U","V","W","X","Y"][i]; return revealedQ1.hasOwnProperty(id) ? revealedQ1[id] : -1 }
    function hCmpVal(i) { let pair = ["T-U", "U-V", "W-X", "X-Y"][i]; return revealedQ2.hasOwnProperty(pair) ? revealedQ2[pair] : 0 }
    function vCmpVal(i) { let pair = ["T-W", "U-X", "V-Y"][i]; return revealedQ2.hasOwnProperty(pair) ? revealedQ2[pair] : 0 }
    function colCount(i) { let id = ["A","B","C","D","E","F","G","H","I"][i]; return revealedQ3.hasOwnProperty(id) ? String(revealedQ3[id]) : "" }
    function rowCount(i) { let id = ["J","K","L","M","N","O","P","Q","R","S"][i]; return revealedQ3.hasOwnProperty(id) ? String(revealedQ3[id]) : "" }
    function getQ4Color(id) { if (!revealedQ4.hasOwnProperty(id)) return ""; return revealedQ4[id] === true ? "#10b981" : "#ef4444" }

    // Các Component UI phụ trợ
    component HArrowPairAuto: Item { width: 36; height: 96; property int cmpVal: 0; Column { anchors.centerIn: parent; spacing: 6; Rectangle { width: 20; height: 20; radius: 4; border.width: 1; visible: cmpVal === 1; color: "#b066ff"; border.color: "#9a4cee"; Text { anchors.centerIn: parent; text: ">"; color: "#fff"; font.pixelSize: 13; font.bold: true; font.family: "Courier New" } } Rectangle { width: 20; height: 20; radius: 4; border.width: 1; visible: cmpVal === -1; color: "#b066ff"; border.color: "#9a4cee"; Text { anchors.centerIn: parent; text: "<"; color: "#fff"; font.pixelSize: 13; font.bold: true; font.family: "Courier New" } } } }
    component VArrowPairAuto: Item { width: 56; height: 36; property int cmpVal: 0; Row { anchors.centerIn: parent; spacing: 16; Rectangle { width: 20; height: 20; radius: 4; border.width: 1; visible: cmpVal === 1; rotation: 90; color: "#b066ff"; border.color: "#9a4cee"; Text { anchors.centerIn: parent; text: ">"; color: "#fff"; font.pixelSize: 13; font.bold: true; font.family: "Courier New" } } Rectangle { width: 20; height: 20; radius: 4; border.width: 1; visible: cmpVal === -1; rotation: 90; color: "#b066ff"; border.color: "#9a4cee"; Text { anchors.centerIn: parent; text: "<"; color: "#fff"; font.pixelSize: 13; font.bold: true; font.family: "Courier New" } } } }
    component TopEODot: Rectangle { width: 24; height: 20; radius: 4; border.width: 1; property string dotType: "even"; color: "#b066ff"; border.color: "#9a4cee"; Text { anchors.centerIn: parent; text: dotType === "even" ? ".." : "."; color: "#fff"; font.pixelSize: 12; font.bold: true; font.letterSpacing: dotType === "even" ? 2 : 0 } }
    component TopCounterBox: Rectangle { property string val: ""; width: 28; height: 22; border.color: "#777"; border.width: 1; radius: 2; color: val !== "" ? "#b066ff" : "#fff"; Text { anchors.centerIn: parent; text: val; font.pixelSize: 11; font.bold: true; color: parent.color === "#b066ff" ? "#fff" : "#333" } }

    // ==========================================
    // KHU VỰC CHỨA BẢNG MẠCH - TỰ ĐỘNG AUTO-SCALE
    // ==========================================
    Item {
        id: scaleContainer
        width: 400  // Base Width lý tưởng
        height: 520 // Base Height lý tưởng
        anchors.centerIn: parent

        // Thuật toán: Lấy tỉ lệ nhỏ nhất giữa chiều rộng/cao cửa sổ so với kích thước gốc -> Đảm bảo luôn nằm gọn trong tab không bị méo.
        scale: Math.min(root.width / width, root.height / height) * 0.95
        transformOrigin: Item.Center


        // 2. SA BÀN LED
        Column {
            id: boardCol
            anchors.top: parent.top
            anchors.topMargin: 15
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 0

            // HÀNG NÚT CỘT A-I
            Row {
                anchors.horizontalCenter: parent.horizontalCenter; spacing: 0
                Item { width: 79; height: 24 }
                Row { spacing: 2; Repeater { model: ["A","B","C"]; delegate: LogicButton { label: modelData; enabled: root.gameActive; opacity: root.gameActive ? 1.0 : 0.4; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } } }
                Item { width: 28; height: 1 }
                Row { spacing: 2; Repeater { model: ["D","E","F"]; delegate: LogicButton { label: modelData; enabled: root.gameActive; opacity: root.gameActive ? 1.0 : 0.4; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } } }
                Item { width: 28; height: 1 }
                Row { spacing: 2; Repeater { model: ["G","H","I"]; delegate: LogicButton { label: modelData; enabled: root.gameActive; opacity: root.gameActive ? 1.0 : 0.4; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } } }
            }

            // HÀNG 1: T, U, V
            Row {
                spacing: 0; anchors.horizontalCenter: parent.horizontalCenter; topPadding: 8
                Item {
                    width: 62; height: 96
                    Repeater { model: rowBtn1Names; delegate: Item { y: rowBtnY[index]; height: 24; width: 62; LogicButton { x: 0; y: 0; label: modelData; enabled: root.gameActive; opacity: root.gameActive ? 1.0 : 0.4; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } TopCounterBox { x: 28; y: 0; val: root.rowCount(index) } } }
                }
                Item { width: 18; height: 1 }
                Row {
                    spacing: 0
                    Repeater {
                        model: 3
                        delegate: Row {
                            required property int index; spacing: 0
                            Item {
                                width: 56; height: 96
                                Rectangle { x: -22; y: -2; width: 18; height: 18; color: "#888"; radius: 2; Text { anchors.centerIn: parent; text: ["T","U","V"][index]; color: "white"; font.pixelSize: 11; font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New" } MouseArea { anchors.fill: parent; enabled: root.gameActive; onClicked: gameBoard.handleButtonPress("SW", ["T","U","V"][index]) } }
                                LedDisplay { anchors.fill: parent; interactive: root.gameActive; ledIndex: index }
                                TopEODot { x: (56 - width) / 2; y: 26 - height / 2; dotType: "even"; visible: root.evenOdd(index) === 0 }
                                TopEODot { x: (56 - width) / 2; y: 69 - height / 2; dotType: "odd"; visible: root.evenOdd(index) === 1 }
                            }
                            HArrowPairAuto { visible: index < 2; width: visible ? 36 : 0; cmpVal: index < 2 ? root.hCmpVal(index) : 0 }
                        }
                    }
                }
            }

            // MŨI TÊN DỌC
            Row {
                anchors.horizontalCenter: parent.horizontalCenter; spacing: 0; topPadding: 8; bottomPadding: 8
                Item { width: 78; height: 36 }
                Repeater { model: 3; delegate: Row { spacing: 0; VArrowPairAuto { cmpVal: root.vCmpVal(index) } Item { visible: index < 2; width: visible ? 36 : 0; height: 1 } } }
            }

            // HÀNG 2: W, X, Y
            Row {
                spacing: 0; anchors.horizontalCenter: parent.horizontalCenter
                Item {
                    width: 62; height: 96
                    Repeater { model: rowBtn2Names; delegate: Item { y: rowBtnY[index]; height: 24; width: 62; LogicButton { x: 0; y: 0; label: modelData; enabled: root.gameActive; opacity: root.gameActive ? 1.0 : 0.4; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } TopCounterBox { x: 28; y: 0; val: root.rowCount(index + 5) } } }
                }
                Item { width: 18; height: 1 }
                Row {
                    spacing: 0
                    Repeater {
                        model: 3
                        delegate: Row {
                            required property int index; spacing: 0
                            Item {
                                width: 56; height: 130
                                Rectangle { x: -22; y: -2; width: 18; height: 18; color: "#888"; radius: 2; Text { anchors.centerIn: parent; text: ["W","X","Y"][index]; color: "white"; font.pixelSize: 11; font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New" } MouseArea { anchors.fill: parent; enabled: root.gameActive; onClicked: gameBoard.handleButtonPress("SW", ["W","X","Y"][index]) } }
                                LedDisplay { x: 0; y: 0; width: 56; height: 96; interactive: root.gameActive; ledIndex: index + 3 }
                                TopEODot { x: (56 - width) / 2; y: 26 - height / 2; dotType: "even"; visible: root.evenOdd(index + 3) === 0 }
                                TopEODot { x: (56 - width) / 2; y: 69 - height / 2; dotType: "odd"; visible: root.evenOdd(index + 3) === 1 }
                                Row { y: 102; anchors.horizontalCenter: parent.horizontalCenter; spacing: 0; TopCounterBox { val: root.colCount(index * 3) } TopCounterBox { val: root.colCount(index * 3 + 1) } TopCounterBox { val: root.colCount(index * 3 + 2) } }
                            }
                            HArrowPairAuto { visible: index < 2; width: visible ? 36 : 0; cmpVal: index < 2 ? root.hCmpVal(index + 2) : 0 }
                        }
                    }
                }
            }
        }
    }
}