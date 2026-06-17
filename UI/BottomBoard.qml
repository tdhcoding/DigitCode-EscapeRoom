import QtQuick
import QtQuick.Controls

Item {
    id: root

    readonly property var rowBtn1Names: ["J","K","L","M","N"]
    readonly property var rowBtn2Names: ["O","P","Q","R","S"]

    function onColBtn(label, btnState) { gameBoard.tapColBtn(label, btnState, false) }
    function onRowBtn(label, btnState, isRow2) { gameBoard.tapRowBtn(label, btnState, isRow2, false) }

    component HArrowPair: Item {
        width: 36; height: 96
        Column {
            anchors.centerIn: parent; spacing: 6
            CmpArrow { id: hGt; arrowVal: "gt"; onTapped: { if (hGt.selected) hLt.selected = false } }
            CmpArrow { id: hLt; arrowVal: "lt"; onTapped: { if (hLt.selected) hGt.selected = false } }
        }
    }

    component VArrowPair: Item {
        width: 56; height: 36
        Row {
            anchors.centerIn: parent; spacing: 10
            CmpArrow { id: vDn; arrowVal: "gt"; rotation: 90; onTapped: { if (vDn.selected) vUp.selected = false } }
            CmpArrow { id: vUp; arrowVal: "lt"; rotation: 90; onTapped: { if (vUp.selected) vDn.selected = false } }
        }
    }

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: mainCol.height + 40
        clip: true

        Column {
            id: mainCol
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 5
            topPadding: 16

            // ── HÀNG NÚT CỘT A-I ──
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 36
                Rectangle {
                    width: 80; height: 32; color: "#e5e5e5"; radius: 4
                    Row { anchors.centerIn: parent; spacing: 4; Repeater { model: ["A","B","C"]; delegate: LogicButton { label: modelData; onTapped: root.onColBtn(label, btnState) } } }
                }
                Rectangle {
                    width: 80; height: 32; color: "#e5e5e5"; radius: 4
                    Row { anchors.centerIn: parent; spacing: 4; Repeater { model: ["D","E","F"]; delegate: LogicButton { label: modelData; onTapped: root.onColBtn(label, btnState) } } }
                }
                Rectangle {
                    width: 80; height: 32; color: "#e5e5e5"; radius: 4
                    Row { anchors.centerIn: parent; spacing: 4; Repeater { model: ["G","H","I"]; delegate: LogicButton { label: modelData; onTapped: root.onColBtn(label, btnState) } } }
                }
            }

            // ── HÀNG 1: T, U, V (DraftGrid nằm DƯỚI) ──
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 20

                // Cột trái: J-N (Bọc Item ảo để chống lỗi Row QML)
                Item {
                    width: 34; height: 164 // Cùng chiều cao với cụm LED bên cạnh
                    Rectangle {
                        width: 34; height: 144; y: 0 // Đẩy khối xám lên đỉnh để căn tâm hoàn hảo với LED
                        color: "#e5e5e5"; radius: 4
                        Column {
                            anchors.centerIn: parent; spacing: 4
                            Repeater { model: rowBtn1Names; delegate: LogicButton { label: modelData; onTapped: root.onRowBtn(label, btnState, false) } }
                        }
                    }
                }

                // Cụm giữa: LED + DraftGrid
                Row {
                    spacing: 0
                    Repeater {
                        model: 3
                        delegate: Row {
                            spacing: 0
                            Item {
                                width: 76; height: 164
                                Rectangle {
                                    x: -11; y: 23; width: 20; height: 18
                                    color: "#888888"; radius: 2
                                    Text { anchors.centerIn: parent; text: ["T","U","V"][index]; color: "white"; font.pixelSize: 11; font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New" }
                                }

                                LedDisplay {
                                    id: ledDisplayRow1
                                    anchors.horizontalCenter: parent.horizontalCenter; y: 24
                                    interactive: true; ledIndex: index + 6
                                }

                                DraftGrid {
                                    anchors.horizontalCenter: parent.horizontalCenter; y: 128 // Nằm dưới LED
                                    filterEven: ledDisplayRow1.isEvenSelected
                                    filterOdd: ledDisplayRow1.isOddSelected
                                    property var backupSegState: []
                                    property bool isAutoDisplaying: false
                                    onExactOneNumberFound: function(number) {
                                        if (!isAutoDisplaying) { backupSegState = gameBoard.getSegState(ledDisplayRow1.ledIndex); isAutoDisplaying = true; }
                                        gameBoard.setLedDigit(ledDisplayRow1.ledIndex, number)
                                    }
                                    onMultipleNumbersFound: {
                                        if (isAutoDisplaying) { gameBoard.setLedSegState(ledDisplayRow1.ledIndex, backupSegState); isAutoDisplaying = false; }
                                    }
                                }
                            }
                            HArrowPair { visible: index < 2; width: visible ? 36 : 0; y: 24 } // Mũi tên ngang theo y của LED
                        }
                    }
                }

                // Cột phải: CounterBoxes
                Item {
                    width: 28; height: 164
                    Column {
                        y: 7; spacing: 0; anchors.horizontalCenter: parent.horizontalCenter
                        Repeater { model: 5; delegate: CounterBox { width: 28; height: 26 } }
                    }
                }
            }

            // ── MŨI TÊN DỌC ──
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 20
                Item { width: 34; height: 36 } // Spacer bù cột J-N
                Row {
                    spacing: 0
                    Repeater {
                        model: 3
                        delegate: Row {
                            spacing: 0
                            Item { width: 76; height: 36; VArrowPair { anchors.centerIn: parent } }
                            Item { visible: index < 2; width: visible ? 36 : 0; height: 1 }
                        }
                    }
                }
                Item { width: 28; height: 36 } // Spacer bù cột Counters
            }

            // ── HÀNG 2: W, X, Y (DraftGrid nằm TRÊN) ──
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 20

                // Cột trái: O-S (Bọc Item ảo)
                Item {
                    width: 34; height: 180 // Chiều cao tổng của Draft(36) + LED(96) + Cụm hộp vuông đáy (26)
                    Rectangle {
                        width: 34; height: 144
                        y: 20 // TỌA ĐỘ VÀNG: Đẩy cụm O-S xuống đúng 20px để căn giữa tuyệt đối với đèn LED nằm ở bên phải
                        color: "#e5e5e5"; radius: 4
                        Column {
                            anchors.centerIn: parent; spacing: 4
                            Repeater { model: rowBtn2Names; delegate: LogicButton { label: modelData; onTapped: root.onRowBtn(label, btnState, true) } }
                        }
                    }
                }

                // Cụm giữa: DraftGrid + LED + Counters
                Row {
                    spacing: 0
                    Repeater {
                        model: 3
                        delegate: Row {
                            spacing: 0
                            Item {
                                width: 76; height: 180

                                DraftGrid {
                                    anchors.horizontalCenter: parent.horizontalCenter; y: 0 // DraftGrid trên cùng
                                    filterEven: ledDisplayRow2.isEvenSelected
                                    filterOdd: ledDisplayRow2.isOddSelected
                                    property var backupSegState: []
                                    property bool isAutoDisplaying: false
                                    onExactOneNumberFound: function(number) {
                                        if (!isAutoDisplaying) { backupSegState = gameBoard.getSegState(ledDisplayRow2.ledIndex); isAutoDisplaying = true; }
                                        gameBoard.setLedDigit(ledDisplayRow2.ledIndex, number)
                                    }
                                    onMultipleNumbersFound: {
                                        if (isAutoDisplaying) { gameBoard.setLedSegState(ledDisplayRow2.ledIndex, backupSegState); isAutoDisplaying = false; }
                                    }
                                }

                                Rectangle {
                                    x: -10; y: 42; width: 18; height: 18
                                    color: "#888888"; radius: 2
                                    Text { anchors.centerIn: parent; text: ["W","X","Y"][index]; color: "white"; font.pixelSize: 11; font.family: Qt.platform.os === "osx" ? "Menlo" : "Courier New" }
                                }

                                LedDisplay {
                                    id: ledDisplayRow2
                                    anchors.horizontalCenter: parent.horizontalCenter; y: 44 // Đèn LED ở giữa
                                    interactive: true; ledIndex: index + 9
                                }

                                // Cụm 3 hộp CounterBoxes đáy liền nhau
                                Row {
                                    anchors.horizontalCenter: parent.horizontalCenter; y: 154; spacing: 0
                                    CounterBox { width: 25; height: 26 }
                                    CounterBox { width: 25; height: 26 }
                                    CounterBox { width: 25; height: 26 }
                                }
                            }
                            HArrowPair { visible: index < 2; width: visible ? 36 : 0; y: 44 } // Mũi tên bám theo y của LED
                        }
                    }
                }

                // Cột phải: CounterBoxes
                Item {
                    width: 28; height: 180
                    Column {
                        y: 30; spacing: 0; anchors.horizontalCenter: parent.horizontalCenter // Căn tâm theo LED giống khối O-S
                        Repeater { model: 5; delegate: CounterBox { width: 28; height: 26 } }
                    }
                }
            }
        }
    }
}