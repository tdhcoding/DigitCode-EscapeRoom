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

    // Phần cứng giữ nút NEW GAME 5 giây -> backend đã sinh đề mới -> nếu QML đang
    // đứng ở màn hình khác (Menu/Ready/Result) thì tự điều hướng về màn hình game
    // để 2 bên luôn là bản sao của nhau (mirror mode).
    // Luồng READY/Play Again của QML không bị ảnh hưởng: các luồng đó điều hướng
    // TRƯỚC rồi mới gọi generateRandomPuzzle(), nên lúc tín hiệu bắn ra thì
    // currentItem đã là screenGame và handler này không làm gì.
    Connections {
        target: gameBoard
        function onPuzzleGenerated() {
            if (!stackView.currentItem || stackView.currentItem.objectName !== "screenGame") {
                stackView.clear()
                // gameActive phải truyền sẵn = true: màn hình mới được tạo SAU khi
                // tín hiệu puzzleGenerated đã bắn nên không tự nhận được nữa
                stackView.push("ScreenGame.qml", { "realLifeMode": hwServer.connected, "gameActive": true })
            }
        }
    }
}