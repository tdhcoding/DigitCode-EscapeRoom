import QtQuick

Item {
    id: root
    width: 56
    height: 96

    property int ledIndex: 0       // 0=T, 1=U, 2=V, 3=W, 4=X, 5=Y
    property bool interactive: false
    property int holdDuration: 1000

    property var segState: []

    Component.onCompleted: {
        segState = gameBoard.getSegState(root.ledIndex)
    }

    Connections {
        target: gameBoard
        function onSegStateUpdated(ledIdx, state) {
            if (ledIdx === root.ledIndex) {
                root.segState = state
            }
        }
    }

    // Tông tối: nét ĐÃ VẼ (state 1) = hổ phách, nét KHOÁ (state 2) = đỏ, TẮT = mờ nền.
    function segColor(idx) {
        if (segState[idx] === 2) return "#e5484d"   // khoá (Q3 full)
        if (segState[idx] > 0)   return "#ffb000"   // đã vẽ
        return "#241a05"                             // tắt (mờ)
    }
    function segGlow(idx) {
        return segState[idx] > 0
    }

    function tapSeg(idx) {
        if (!interactive) return
        gameBoard.tapSegment(ledIndex, idx)
    }
    function holdSeg(idx) {
        if (!interactive) return
        gameBoard.holdSegment(ledIndex, idx)
    }
    function turnOnGroup(segs)          { gameBoard.turnOnGroupQml(ledIndex, segs) }
    function restoreGroup(segs, backup) { gameBoard.restoreGroupQml(ledIndex, segs, backup) }

    // Segment bo tròn (Rectangle radius) thay cho Shape lục giác — theo layout redesign.
    component RSeg: Rectangle {
        property int segIdx: 0
        radius: Math.min(width, height) / 2
        color: root.segColor(segIdx)
        antialiasing: true
        // Glow nhẹ khi sáng (nhiều lớp Rectangle mờ = tương đương MultiEffect nhẹ)
        Rectangle {
            anchors.centerIn: parent
            width: parent.width + 6; height: parent.height + 6
            radius: parent.radius + 3
            color: "transparent"
            border.width: 3
            border.color: "#ffb000"
            opacity: root.segGlow(parent.segIdx) ? 0.18 : 0
            antialiasing: true
        }
        MouseArea {
            anchors.fill: parent
            anchors.margins: -2
            pressAndHoldInterval: root.holdDuration
            property bool wasHeld: false
            onPressAndHold: { wasHeld = true; root.holdSeg(parent.segIdx) }
            onReleased: { if (!wasHeld) root.tapSeg(parent.segIdx); wasHeld = false }
        }
    }

    RSeg { segIdx: 0; x: 9;  y: 0;  width: 38; height: 10 }   // A
    RSeg { segIdx: 1; x: 46; y: 8;  width: 10; height: 38 }   // B
    RSeg { segIdx: 2; x: 46; y: 50; width: 10; height: 38 }   // C
    RSeg { segIdx: 3; x: 9;  y: 86; width: 38; height: 10 }   // D
    RSeg { segIdx: 4; x: 0;  y: 50; width: 10; height: 38 }   // E
    RSeg { segIdx: 5; x: 0;  y: 8;  width: 10; height: 38 }   // F
    RSeg { segIdx: 6; x: 9;  y: 43; width: 38; height: 10 }   // G
}
