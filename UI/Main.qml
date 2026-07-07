import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: mainWindow
    width: 580
    height: 650
    visible: true
    title: "Digit Code SINGLE v5"
    color: "#ffffff"

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: "ScreenMenu.qml" // Khởi động lên là vào Menu đầu tiên
    }
}