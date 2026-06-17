import QtQuick
import QtQuick.Shapes

Item {
    id: root
    width: 56
    height: 96

    property int ledIndex: 0       // 0=T, 1=U, 2=V, 3=W, 4=X, 5=Y
    property bool interactive: false
    property int holdDuration: 1000

    property var segState: []
    property alias isEvenSelected: dotEven.selected
    property alias isOddSelected: dotOdd.selected

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

    readonly property real opOn:  0.85
    readonly property real opOff: 0.08

    function segColor(idx) {
        return segState[idx] === 2 ? "#ef4444" : "#111111"
    }

    function segOpacity(idx) {
        return segState[idx] > 0 ? opOn : opOff
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

    component HSegment: Shape {
        property int segIdx: 0
        width: 38; height: 10
        opacity: root.segOpacity(segIdx)
        ShapePath {
            fillColor: root.segColor(segIdx)  // ← đổi parent.segIdx thành segIdx
            strokeColor: "transparent"
            startX: 3.8; startY: 0
            PathLine { x: 34.2; y: 0  }
            PathLine { x: 38;   y: 5  }
            PathLine { x: 34.2; y: 10 }
            PathLine { x: 3.8;  y: 10 }
            PathLine { x: 0;    y: 5  }
            PathLine { x: 3.8;  y: 0  }
        }
        MouseArea {
            anchors.fill: parent
            pressAndHoldInterval: root.holdDuration
            property bool wasHeld: false
            onPressAndHold: {
                wasHeld = true
                root.holdSeg(parent.segIdx)
            }
            onReleased: {
                if (!wasHeld) root.tapSeg(parent.segIdx)
                wasHeld = false
            }
        }
    }

    component VSegment: Shape {
        property int segIdx: 0
        width: 10; height: 38
        opacity: root.segOpacity(segIdx)
        ShapePath {
            fillColor: root.segColor(segIdx)  // ← đổi parent.segIdx thành segIdx
            strokeColor: "transparent"
            startX: 0; startY: 3.8
            PathLine { x: 5;  y: 0    }
            PathLine { x: 10; y: 3.8  }
            PathLine { x: 10; y: 34.2 }
            PathLine { x: 5;  y: 38   }
            PathLine { x: 0;  y: 34.2 }
            PathLine { x: 0;  y: 3.8  }
        }
        MouseArea {
            anchors.fill: parent
            pressAndHoldInterval: root.holdDuration
            property bool wasHeld: false
            onPressAndHold: {
                wasHeld = true
                root.holdSeg(parent.segIdx)
            }
            onReleased: {
                if (!wasHeld) root.tapSeg(parent.segIdx)
                wasHeld = false
            }
        }
    }

    HSegment { segIdx: 0; x: 9;  y: 0  }   // A
    VSegment { segIdx: 1; x: 46; y: 8  }   // B
    VSegment { segIdx: 2; x: 46; y: 50 }   // C
    HSegment { segIdx: 3; x: 9;  y: 86 }   // D
    VSegment { segIdx: 4; x: 0;  y: 50 }   // E
    VSegment { segIdx: 5; x: 0;  y: 8  }   // F
    HSegment { segIdx: 6; x: 9;  y: 43 }   // G

    // Chấm chẵn/lẻ
    EODot {
        id: dotEven
        x: (root.width - width) / 2
        y: 26 - height / 2
        dotType: "even"
        visible: interactive
        onTapped: { if (dotEven.selected) dotOdd.selected = false }
    }

    EODot {
        id: dotOdd
        x: (root.width - width) / 2
        y: 69 - height / 2
        dotType: "odd"
        visible: interactive
        onTapped: { if (dotOdd.selected) dotEven.selected = false }
    }
}