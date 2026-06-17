import QtQuick
import QtQuick.Controls

Window {
    id: root
    width: 580
    height: 650
    visible: true
    title: "Digit Code"
    color: "#000000"

    Column {
        anchors.fill: parent
        spacing: 0

        // ── TOP SECTION (nền xám) ──
        Rectangle {
            width: parent.width
            height: parent.height * 0.42
            color: "#d3d3d3"

            TopBoard {
                anchors.fill: parent
                anchors.margins: 10
            }
        }

        // Divider
        Rectangle {
            width: parent.width
            height: 4
            color: "#888"
        }

        // ── BOTTOM SECTION (nền trắng) ──
        Rectangle {
            width: parent.width
            height: parent.height * 0.58 - 4
            color: "#ffffff"

            BottomBoard {
                anchors.fill: parent
            }
        }
    }
}