import QtQuick

Item {
    id: root
    width: 76
    height: 36

    // Nhận cờ hiệu từ LedDisplay truyền vào
    property bool filterEven: false
    property bool filterOdd: false

    // 1. Mảng lưu vết những số do người dùng click thủ công (false = bình thường, true = gạch)
    property var manualCrossedStates: [false, false, false, false, false, false, false, false, false, false]

    readonly property var numMap: [0, 2, 4, 6, 8, 1, 3, 5, 7, 9]

    signal exactOneNumberFound(int number)
    signal multipleNumbersFound()

    // 2. LOGIC TỰ ĐỘNG CẬP NHẬT: Kết hợp giữa trạng thái thủ công và bộ lọc Even/Odd
    readonly property var effectiveCrossedStates: {
        let arr = [];
        for (let i = 0; i < 10; i++) {
            let isNumOdd = (numMap[i] % 2 !== 0);
            // Nếu Even bật -> tự động gạch số lẻ. Nếu Odd bật -> tự động gạch số chẵn.
            let autoCrossed = (filterEven && isNumOdd) || (filterOdd && !isNumOdd);

            // Một số được coi là gạch nếu gạch thủ công HOẶC gạch tự động từ bộ lọc
            arr.push(manualCrossedStates[i] || autoCrossed);
        }
        return arr;
    }

    // 3. LOGIC THEO DÕI SỐ LƯỢNG: Tính toán dựa trên mảng trạng thái thực tế tổng hợp ở trên
    onEffectiveCrossedStatesChanged: {
        let uncrossedNumbers = []
        for (let i = 0; i < 10; i++) {
            if (!effectiveCrossedStates[i]) {
                uncrossedNumbers.push(numMap[i])
            }
        }

        if (uncrossedNumbers.length === 1) {
            root.exactOneNumberFound(uncrossedNumbers[0]) // Đổi LED thành số này
        } else {
            root.multipleNumbersFound() // Khôi phục lại vạch LED cũ
        }
    }

    // Vẽ viền nét đứt
    Canvas {
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            ctx.strokeStyle = "#a0a0a0";
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 3]);
            ctx.lineJoin = "round";
            ctx.beginPath();
            ctx.roundedRect(0, 0, width, height, 4, 4);
            ctx.stroke();
        }
    }

    Grid {
        anchors.centerIn: parent
        columns: 5
        spacing: 5
        rowSpacing: 2

        Repeater {
            model: 10
            delegate: Item {
                width: 10; height: 12

                // Hiển thị giao diện dựa vào mảng tổng hợp thực tế
                property bool isCrossed: root.effectiveCrossedStates[index]

                Text {
                    anchors.centerIn: parent
                    text: root.numMap[index]
                    font.pixelSize: 11
                    font.bold: true
                    color: parent.isCrossed ? "#ef4444" : "#333333"
                    font.strikeout: parent.isCrossed
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        // Khi người dùng click, ta chỉ đảo trạng thái trong mảng thủ công
                        let arr = root.manualCrossedStates.slice()
                        arr[index] = !arr[index]
                        root.manualCrossedStates = arr
                    }
                }
            }
        }
    }
}