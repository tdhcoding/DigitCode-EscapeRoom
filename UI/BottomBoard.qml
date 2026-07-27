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

    readonly property string monoFont: Qt.platform.os === "osx" ? "Menlo" : "Courier New"

    // ===== Hàm tra dữ liệu (GIỮ NGUYÊN so với bản gốc) =====
    function evenOdd(i) { let id = ["T","U","V","W","X","Y"][i]; return revealedQ1.hasOwnProperty(id) ? revealedQ1[id] : -1 }
    function hCmpVal(i) { let pair = ["T-U", "U-V", "W-X", "X-Y"][i]; return revealedQ2.hasOwnProperty(pair) ? revealedQ2[pair] : 0 }
    function vCmpVal(i) { let pair = ["T-W", "U-X", "V-Y"][i]; return revealedQ2.hasOwnProperty(pair) ? revealedQ2[pair] : 0 }
    function colCount(i) { let id = ["A","B","C","D","E","F","G","H","I"][i]; return revealedQ3.hasOwnProperty(id) ? String(revealedQ3[id]) : "" }
    function rowCount(i) { let id = ["J","K","L","M","N","O","P","Q","R","S"][i]; return revealedQ3.hasOwnProperty(id) ? String(revealedQ3[id]) : "" }
    function getQ4Color(id) { if (!revealedQ4.hasOwnProperty(id)) return ""; return revealedQ4[id] === true ? "#b7d84b" : "#e5484d" }

    // ===== Component phụ trợ (tông tối) =====

    // Q1 (chẵn/lẻ): GIỮ NGUYÊN ".." (even) / "." (odd), chỉ đổi màu.
    component EODotBox: Rectangle {
        property string dotType: "even"
        width: 24; height: 20; radius: 6; color: "#ff6a1a"; z: 4; antialiasing: true
        Text {
            anchors.centerIn: parent
            text: dotType === "even" ? ".." : "."
            color: "#1a0f04"; font.pixelSize: 13; font.bold: true
            font.letterSpacing: dotType === "even" ? 2 : 0
        }
    }

    // Q2 (lớn/bé) ngang: GIỮ NGUYÊN mũi tên ĐƠN > hoặc <.
    component HArrow: Item {
        id: ha
        property int cmpVal: 0
        width: 36; height: 108
        Rectangle {
            anchors.centerIn: parent
            width: 26; height: 24; radius: 8; antialiasing: true
            visible: ha.cmpVal !== 0
            color: "#ff6a1a"
            Text { anchors.centerIn: parent; text: ha.cmpVal === 1 ? ">" : "<"; color: "#1a0f04"; font.pixelSize: 14; font.bold: true; font.family: root.monoFont }
        }
    }

    // Q2 (lớn/bé) dọc: GIỮ NGUYÊN mũi tên ĐƠN xoay 90°.
    component VArrow: Item {
        id: va
        property int cmpVal: 0
        width: 68; height: 40
        Rectangle {
            anchors.centerIn: parent
            width: 26; height: 24; radius: 8; antialiasing: true
            rotation: 90
            visible: va.cmpVal !== 0
            color: "#ff6a1a"
            Text { anchors.centerIn: parent; text: va.cmpVal === 1 ? ">" : "<"; color: "#1a0f04"; font.pixelSize: 14; font.bold: true; font.family: root.monoFont }
        }
    }

    // Q3 (đếm): ô counter, có số = sáng, trống = mờ.
    component CBox: Rectangle {
        property string val: ""
        width: 20; height: 20; radius: 5; antialiasing: true
        color: val !== "" ? "#2a2416" : "#141009"
        border.width: 2; border.color: val !== "" ? "#5a4a28" : "#4a3f28"
        Text { anchors.centerIn: parent; text: val; color: "#ffb000"; font.pixelSize: 11; font.bold: true; font.family: root.monoFont }
    }

    // LED bo tròn: bezel + LedDisplay + tab chọn + 2 vị trí EO (hiện 1 theo parity).
    component Cell: Item {
        id: cell
        property int ledIndex: 0
        property string label: "T"
        width: 68; height: 108
        Rectangle { anchors.fill: parent; radius: 12; color: "#0c0a05"; border.width: 2; border.color: "#3a3018"; antialiasing: true }
        LedDisplay { anchors.centerIn: parent; width: 56; height: 96; ledIndex: cell.ledIndex; interactive: root.gameActive }
        Rectangle {
            x: 4; y: 4; width: 18; height: 18; radius: 6; color: "#7a6a3a"; z: 5; antialiasing: true
            Text { anchors.centerIn: parent; text: cell.label; color: "#141009"; font.pixelSize: 11; font.bold: true; font.family: root.monoFont }
            MouseArea { anchors.fill: parent; enabled: root.gameActive; onClicked: gameBoard.handleButtonPress("SW", cell.label) }
        }
        EODotBox { anchors.horizontalCenter: parent.horizontalCenter; y: 24; dotType: "even"; visible: root.evenOdd(cell.ledIndex) === 0 }
        EODotBox { anchors.horizontalCenter: parent.horizontalCenter; y: 64; dotType: "odd";  visible: root.evenOdd(cell.ledIndex) === 1 }
    }

    component ColBtn: LogicButton {
        width: 20; height: 20
        enabled: root.gameActive
        opacity: root.gameActive ? 1.0 : 0.4
    }

    // ===== Khu bảng, tự động scale cho vừa =====
    Item {
        id: scaleContainer
        width: 360; height: 350
        anchors.centerIn: parent
        scale: Math.min(root.width / width, root.height / height) * 0.96
        transformOrigin: Item.Center

        Column {
            id: boardCol
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top; anchors.topMargin: 6
            spacing: 8

            // --- Hàng nút cột A-I ---
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 0
                Item { width: 34; height: 22 }
                Repeater {
                    model: [["A","B","C"], ["D","E","F"], ["G","H","I"]]
                    delegate: Row {
                        id: grp
                        required property var modelData
                        required property int index
                        spacing: 0
                        Item {
                            width: 68; height: 22
                            Row {
                                anchors.centerIn: parent; spacing: 5
                                Repeater {
                                    model: grp.modelData
                                    delegate: ColBtn { required property string modelData; label: modelData; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) }
                                }
                            }
                        }
                        Item { width: 36; height: 1; visible: grp.index < 2 }
                    }
                }
                Item { width: 38; height: 1 }
            }

            // --- Khu giữa: [nút hàng trái] [LED + mũi tên] [counter hàng phải] ---
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 12

                // Nút hàng J-N / O-S (trái)
                Column {
                    spacing: 40
                    Column {
                        spacing: 2
                        Repeater { model: root.rowBtn1Names; delegate: ColBtn { label: modelData; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } }
                    }
                    Column {
                        spacing: 2
                        Repeater { model: root.rowBtn2Names; delegate: ColBtn { label: modelData; overrideColor: root.getQ4Color(modelData); onTapped: gameBoard.handleButtonPress("SW", modelData) } }
                    }
                }

                // LED + mũi tên (giữa)
                Column {
                    spacing: 0
                    // hàng 1: T U V
                    Row {
                        spacing: 0
                        Cell { ledIndex: 0; label: "T" }
                        HArrow { cmpVal: root.hCmpVal(0) }
                        Cell { ledIndex: 1; label: "U" }
                        HArrow { cmpVal: root.hCmpVal(1) }
                        Cell { ledIndex: 2; label: "V" }
                    }
                    // mũi tên dọc
                    Row {
                        spacing: 0
                        Repeater {
                            model: 3
                            delegate: Row {
                                required property int index
                                spacing: 0
                                VArrow { cmpVal: root.vCmpVal(index) }
                                Item { width: 36; height: 1; visible: index < 2 }
                            }
                        }
                    }
                    // hàng 2: W X Y
                    Row {
                        spacing: 0
                        Cell { ledIndex: 3; label: "W" }
                        HArrow { cmpVal: root.hCmpVal(2) }
                        Cell { ledIndex: 4; label: "X" }
                        HArrow { cmpVal: root.hCmpVal(3) }
                        Cell { ledIndex: 5; label: "Y" }
                    }
                    // counter cột (9) dưới W/X/Y
                    Row {
                        spacing: 0
                        topPadding: 6
                        Repeater {
                            model: 3
                            delegate: Row {
                                required property int index
                                spacing: 0
                                Item {
                                    width: 68; height: 20
                                    Row {
                                        anchors.centerIn: parent; spacing: 2
                                        CBox { val: root.colCount(index * 3) }
                                        CBox { val: root.colCount(index * 3 + 1) }
                                        CBox { val: root.colCount(index * 3 + 2) }
                                    }
                                }
                                Item { width: 36; height: 1; visible: index < 2 }
                            }
                        }
                    }
                }

                // counter hàng (phải) 5+5
                Column {
                    spacing: 40
                    Column {
                        spacing: 2
                        Repeater { model: 5; delegate: CBox { width: 26; height: 20; val: root.rowCount(index) } }
                    }
                    Column {
                        spacing: 2
                        Repeater { model: 5; delegate: CBox { width: 26; height: 20; val: root.rowCount(index + 5) } }
                    }
                }
            }
        }
    }
}
