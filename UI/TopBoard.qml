import QtQuick
import QtQuick.Controls

Item {
    id: root

    readonly property var rowBtn1Names: ["J","K","L","M","N"]
    readonly property var rowBtn2Names: ["O","P","Q","R","S"]
    readonly property var rowBtnY: [-7, 15, 36, 57, 79]
    readonly property var rowCounterMax: [3, 6, 3, 6, 3]
    readonly property real boardScale: 0.72

    property var topStats: ({})
    property bool hasStats: Object.keys(topStats).length > 0

    function evenOdd(i)  { return hasStats ? topStats.evenOdd[i]   : -1 }
    function hCmpVal(i)  { return hasStats ? topStats.hCmp[i]      :  0 }
    function vCmpVal(i)  { return hasStats ? topStats.vCmp[i]      :  0 }
    function colCount(i) { return hasStats ? topStats.colCounts[i] : "" }
    function rowCount(i) { return hasStats ? topStats.rowCounts[i] : "" }

    Connections {
        target: gameBoard
        function onTopStatsChanged(stats) { root.topStats = stats }
    }

    function validateDigits(raw) {
        let valid = ""
        for (let i = 0; i < raw.length; i++) {
            let ch = raw[i]
            if (valid.length >= 6) break
            let count = valid.split("").filter(c => c === ch).length
            if (count >= 2) continue
            let idx = valid.length
            if (idx % 3 !== 0 && valid[idx - 1] === ch) continue
            if (idx >= 3 && valid[idx - 3] === ch) continue
            valid += ch
        }
        return valid
    }

    // ── HArrowPairAuto ──
    component HArrowPairAuto: Item {
        width: 36; height: 96
        property int cmpVal: 0

        Column {
            anchors.centerIn: parent; spacing: 6

            Rectangle {
                width: 20; height: 20; radius: 4; border.width: 1
                visible: cmpVal === 1
                property bool selected: false
                color: selected ? "#b066ff" : "#e0e0e0"
                border.color: selected ? "#9a4cee" : "#cccccc"
                Text {
                    anchors.centerIn: parent; text: ">"
                    color: parent.selected ? "#fff" : "#777"
                    font.pixelSize: 13; font.bold: true; font.family: "Courier New"
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: parent.selected = !parent.selected
                }
            }

            Rectangle {
                width: 20; height: 20; radius: 4; border.width: 1
                visible: cmpVal === -1
                property bool selected: false
                color: selected ? "#b066ff" : "#e0e0e0"
                border.color: selected ? "#9a4cee" : "#cccccc"
                Text {
                    anchors.centerIn: parent; text: "<"
                    color: parent.selected ? "#fff" : "#777"
                    font.pixelSize: 13; font.bold: true; font.family: "Courier New"
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: parent.selected = !parent.selected
                }
            }
        }
    }

    // ── VArrowPairAuto ──
    component VArrowPairAuto: Item {
        width: 56; height: 36
        property int cmpVal: 0

        Row {
            anchors.centerIn: parent; spacing: 16

            Rectangle {
                width: 20; height: 20; radius: 4; border.width: 1
                visible: cmpVal === 1
                property bool selected: false
                color: selected ? "#b066ff" : "#e0e0e0"
                border.color: selected ? "#9a4cee" : "#cccccc"
                rotation: 90
                Text {
                    anchors.centerIn: parent; text: ">"
                    color: parent.selected ? "#fff" : "#777"
                    font.pixelSize: 13; font.bold: true; font.family: "Courier New"
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: parent.selected = !parent.selected
                }
            }

            Rectangle {
                width: 20; height: 20; radius: 4; border.width: 1
                visible: cmpVal === -1
                property bool selected: false
                color: selected ? "#b066ff" : "#e0e0e0"
                border.color: selected ? "#9a4cee" : "#cccccc"
                rotation: 90
                Text {
                    anchors.centerIn: parent; text: "<"
                    color: parent.selected ? "#fff" : "#777"
                    font.pixelSize: 13; font.bold: true; font.family: "Courier New"
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: parent.selected = !parent.selected
                }
            }
        }
    }

    // ── EODot có thể click ──
    component TopEODot: Rectangle {
        width: 24; height: 20; radius: 4; border.width: 1
        property string dotType: "even"
        property bool selected: false
        color: selected ? "#b066ff" : "#e0e0e0"
        border.color: selected ? "#9a4cee" : "#cccccc"
        Text {
            anchors.centerIn: parent
            text: dotType === "even" ? ".." : "."
            color: parent.selected ? "#fff" : "#777"
            font.pixelSize: 12; font.bold: true
            font.letterSpacing: dotType === "even" ? 2 : 0
        }
        MouseArea {
            anchors.fill: parent
            onClicked: parent.selected = !parent.selected
        }
    }

    // ── Counter box có thể click ──
    component TopCounterBox: Rectangle {
        property string val: ""
        width: 28; height: 22
        border.color: "#777"; border.width: 1; radius: 2
        property bool selected: false
        color: selected ? "#b066ff" : "#fff"
        Text {
            anchors.centerIn: parent
            text: val
            font.pixelSize: 11; font.bold: true
            color: parent.selected ? "#fff" : "#333"
        }
        MouseArea {
            anchors.fill: parent
            enabled: val !== ""
            onClicked: parent.selected = !parent.selected
        }
    }

    // ── Input cố định ──
    Rectangle {
        id: inputBox
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - 20, 400)
        height: 50
        color: "#e9e9e9"; border.color: "#999"; border.width: 2; radius: 5
        z: 10

        TextInput {
            id: codeInput
            anchors.centerIn: parent
            width: parent.width - 20
            font.pixelSize: 24; font.bold: true
            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
            horizontalAlignment: Text.AlignHCenter
            inputMethodHints: Qt.ImhDigitsOnly
            color: "#333"; maximumLength: 12

            Text {
                anchors.centerIn: parent
                text: "ENTER 6 DIGITS..."
                font: parent.font; color: "#aaa"
                visible: parent.text.length === 0
            }

            property bool isUpdating: false
            onTextChanged: {
                if (isUpdating) return
                isUpdating = true
                let raw = text.replace(/[^0-9]/g, "")
                let valid = root.validateDigits(raw)
                if (text !== valid) {
                    let pos = cursorPosition
                    text = valid
                    cursorPosition = Math.min(pos, valid.length)
                }
                gameBoard.setTopDigits(valid)
                isUpdating = false
            }
        }
    }

    // ── Board scroll ──
    Flickable {
        anchors.top: inputBox.bottom
        anchors.topMargin: 8
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        clip: true
        flickableDirection: Flickable.VerticalFlick
        contentWidth: width
        contentHeight: (boardCol.implicitHeight + 20) * boardScale
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        Item {
            width: parent.width
            height: parent.contentHeight

            Column {
                id: boardCol
                scale: boardScale
                transformOrigin: Item.Top
                anchors.horizontalCenter: parent.horizontalCenter
                y: 10; spacing: 0

                // ── HÀNG NÚT CỘT A-I ──
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 0
                    Item { width: 79; height: 24 }
                    Row {
                        spacing: 2
                        Repeater {
                            model: ["A","B","C"]
                            delegate: LogicButton {
                                label: modelData
                                isPurpleToggle: true
                                enabled: root.hasStats
                                opacity: root.hasStats ? 1.0 : 0.4
                            }
                        }
                    }
                    Item { width: 28; height: 1 }
                    Row {
                        spacing: 2
                        Repeater {
                            model: ["D","E","F"]
                            delegate: LogicButton {
                                label: modelData
                                isPurpleToggle: true
                                enabled: root.hasStats
                                opacity: root.hasStats ? 1.0 : 0.4
                            }
                        }
                    }
                    Item { width: 28; height: 1 }
                    Row {
                        spacing: 2
                        Repeater {
                            model: ["G","H","I"]
                            delegate: LogicButton {
                                label: modelData
                                isPurpleToggle: true
                                enabled: root.hasStats
                                opacity: root.hasStats ? 1.0 : 0.4
                            }
                        }
                    }
                }

                // ── HÀNG 1: T, U, V ──
                Row {
                    spacing: 0
                    anchors.horizontalCenter: parent.horizontalCenter
                    topPadding: 8

                    Item {
                        width: 62; height: 96
                        Repeater {
                            model: rowBtn1Names
                            delegate: Item {
                                y: rowBtnY[index]; height: 24; width: 62
                                LogicButton {
                                    x: 0; y: 0; label: modelData
                                    isPurpleToggle: true
                                    enabled: root.hasStats
                                    opacity: root.hasStats ? 1.0 : 0.4
                                }
                                TopCounterBox {
                                    x: 28; y: 0
                                    val: root.hasStats ? String(root.rowCount(index)) : ""
                                }
                            }
                        }
                    }

                    Item { width: 18; height: 1 }

                    Row {
                        spacing: 0
                        Repeater {
                            model: 3
                            delegate: Row {
                                required property int index
                                spacing: 0

                                Item {
                                    width: 56; height: 96

                                    Rectangle {
                                        x: -22; y: -2; width: 18; height: 18
                                        color: "#888"; radius: 2
                                        Text {
                                            anchors.centerIn: parent
                                            text: ["T","U","V"][index]
                                            color: "white"; font.pixelSize: 11
                                            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
                                        }
                                    }

                                    LedDisplay {
                                        anchors.fill: parent
                                        interactive: false
                                        ledIndex: index
                                    }

                                    TopEODot {
                                        x: (56 - width) / 2; y: 26 - height / 2
                                        dotType: "even"
                                        visible: root.hasStats && root.evenOdd(index) === 0
                                    }
                                    TopEODot {
                                        x: (56 - width) / 2; y: 69 - height / 2
                                        dotType: "odd"
                                        visible: root.hasStats && root.evenOdd(index) === 1
                                    }
                                }

                                HArrowPairAuto {
                                    visible: index < 2
                                    width: visible ? 36 : 0
                                    cmpVal: index < 2 ? root.hCmpVal(index) : 0
                                }
                            }
                        }
                    }
                }

                // ── Mũi tên DỌC T-W, U-X, V-Y ──
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 0; topPadding: 8; bottomPadding: 8
                    Item { width: 78; height: 36 }
                    Repeater {
                        model: 3
                        delegate: Row {
                            spacing: 0
                            VArrowPairAuto { cmpVal: root.vCmpVal(index) }
                            Item { visible: index < 2; width: visible ? 36 : 0; height: 1 }
                        }
                    }
                }

                // ── HÀNG 2: W, X, Y ──
                Row {
                    spacing: 0
                    anchors.horizontalCenter: parent.horizontalCenter

                    Item {
                        width: 62; height: 96
                        Repeater {
                            model: rowBtn2Names
                            delegate: Item {
                                y: rowBtnY[index]; height: 24; width: 62
                                LogicButton {
                                    x: 0; y: 0; label: modelData
                                    isPurpleToggle: true
                                    enabled: root.hasStats
                                    opacity: root.hasStats ? 1.0 : 0.4
                                }
                                TopCounterBox {
                                    x: 28; y: 0
                                    val: root.hasStats ? String(root.rowCount(index + 5)) : ""
                                }
                            }
                        }
                    }

                    Item { width: 18; height: 1 }

                    Row {
                        spacing: 0
                        Repeater {
                            model: 3
                            delegate: Row {
                                required property int index
                                spacing: 0

                                Item {
                                    width: 56; height: 130

                                    Rectangle {
                                        x: -22; y: -2; width: 18; height: 18
                                        color: "#888"; radius: 2
                                        Text {
                                            anchors.centerIn: parent
                                            text: ["W","X","Y"][index]
                                            color: "white"; font.pixelSize: 11
                                            font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New"
                                        }
                                    }

                                    LedDisplay {
                                        x: 0; y: 0; width: 56; height: 96
                                        interactive: false
                                        ledIndex: index + 3
                                    }

                                    TopEODot {
                                        x: (56 - width) / 2; y: 26 - height / 2
                                        dotType: "even"
                                        visible: root.hasStats && root.evenOdd(index + 3) === 0
                                    }
                                    TopEODot {
                                        x: (56 - width) / 2; y: 69 - height / 2
                                        dotType: "odd"
                                        visible: root.hasStats && root.evenOdd(index + 3) === 1
                                    }

                                    // Counter cột tự động
                                    Row {
                                        y: 102
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        spacing: 0
                                        TopCounterBox { val: root.hasStats ? String(root.colCount(index * 3))     : "" }
                                        TopCounterBox { val: root.hasStats ? String(root.colCount(index * 3 + 1)) : "" }
                                        TopCounterBox { val: root.hasStats ? String(root.colCount(index * 3 + 2)) : "" }
                                    }
                                }

                                HArrowPairAuto {
                                    visible: index < 2
                                    width: visible ? 36 : 0
                                    cmpVal: index < 2 ? root.hCmpVal(index + 2) : 0
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}