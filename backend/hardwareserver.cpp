#include "hardwareserver.h"
#include <QDebug>
#include <QJsonArray>
#include <QNetworkInterface>

HardwareServer::HardwareServer(GameBoard* board, QObject *parent)
    : QObject(parent), m_board(board)
{
    m_server = new QWebSocketServer(QStringLiteral("Escape Room Server"),
                                    QWebSocketServer::NonSecureMode, this);

    if (m_server->listen(QHostAddress::Any, 8080)) {
        qDebug() << "[NET] Hardware Server is listening on port" << m_server->serverPort();
        connect(m_server, &QWebSocketServer::newConnection, this, &HardwareServer::onNewConnection);
    } else {
        qDebug() << "[NET] Failed to start Hardware Server!";
    }

    // Nối các tín hiệu của GameBoard vào để Server bắt và gửi xuống ESP32
    connect(m_board, &GameBoard::segStateUpdated, this, &HardwareServer::onSegStateUpdated);

    // MỚI: Bắt tín hiệu yêu cầu cập nhật OLED
    connect(m_board, &GameBoard::oledUpdateRequested, this, &HardwareServer::onOledUpdateRequested);

    // Đẩy thời gian/điểm xuống OLED thật mỗi khi thay đổi — OLED ảo trên QML đọc
    // thẳng Q_PROPERTY nên tự có, phần cứng thì phải được "mớm" qua mạng.
    connect(m_board, &GameBoard::playTimeSecondsChanged, this, &HardwareServer::onStatsChanged);
    connect(m_board, &GameBoard::pointsChanged, this, &HardwareServer::onStatsChanged);
}

// Gửi gói {"type":"STATS"} chứa thời gian chơi + điểm hiện tại
void HardwareServer::onStatsChanged() {
    QJsonObject obj;
    obj["type"] = "STATS";
    obj["time"] = m_board->playTimeSeconds();
    obj["points"] = m_board->points();
    sendToHardware(obj);
}

HardwareServer::~HardwareServer() {
    m_server->close();
    qDeleteAll(m_clients.begin(), m_clients.end());
}

void HardwareServer::onNewConnection() {
    QWebSocket *clientSocket = m_server->nextPendingConnection();
    qDebug() << "[NET] ESP32 Connected:" << clientSocket->peerAddress().toString();

    connect(clientSocket, &QWebSocket::textMessageReceived, this, &HardwareServer::processTextMessage);
    connect(clientSocket, &QWebSocket::disconnected, this, &HardwareServer::socketDisconnected);

    m_clients << clientSocket;

    // Gửi thông điệp chào mừng xuống ESP32
    QJsonObject welcome;
    welcome["type"] = "SYSTEM";
    welcome["cmd"] = "welcome";
    welcome["status"] = "connected_to_qt";
    sendToHardware(welcome);

    // Đồng bộ lại toàn bộ trạng thái cho client vừa kết nối (xử lý trường hợp
    // ESP32 rớt WiFi giữa ván rồi reconnect - nếu không "chép bài" lại thì sa bàn
    // thật sẽ giữ trạng thái cũ trước lúc rớt, phá vỡ nguyên tắc mirror).
    for (int led = 0; led < 6; led++) {
        QVariantList state = m_board->getSegState(led);
        for (int s = 0; s < 7; s++) {
            QJsonObject obj;
            obj["type"] = "DRAW";
            obj["ledIdx"] = led;
            obj["segIdx"] = s;
            obj["val"] = state[s].toInt();
            clientSocket->sendTextMessage(QJsonDocument(obj).toJson(QJsonDocument::Compact));
        }
    }

    // Khôi phục dòng chữ OLED cuối cùng (nếu có)
    QJsonObject oled;
    oled["type"] = "OLED";
    if (m_lastOledLine2 == "DEFAULT_LAYOUT" || (m_lastOledLine1.isEmpty() && m_lastOledLine2.isEmpty())) {
        oled["layout"] = "default";
    } else {
        oled["layout"] = "text";
        oled["line1"] = m_lastOledLine1;
        oled["line2"] = m_lastOledLine2;
    }
    clientSocket->sendTextMessage(QJsonDocument(oled).toJson(QJsonDocument::Compact));

    // Đồng bộ luôn thời gian/điểm hiện tại
    onStatsChanged();

    emit connectedChanged();
}

QString HardwareServer::serverAddress() const {
    // Lấy địa chỉ IPv4 (không phải loopback) của máy - chính là giá trị cần
    // điền vào QT_SERVER_IP trong secrets.h của firmware ESP32
    const auto addresses = QNetworkInterface::allAddresses();
    for (const QHostAddress& addr : addresses) {
        if (addr.protocol() == QAbstractSocket::IPv4Protocol && !addr.isLoopback()) {
            return QString("%1:%2").arg(addr.toString()).arg(m_server->serverPort());
        }
    }
    return QString("Không tìm thấy IP (kiểm tra WiFi):%1").arg(m_server->serverPort());
}

// --- TRẠM PHÂN LOẠI DỮ LIỆU TỪ ESP32 GỬI LÊN ---
void HardwareServer::processTextMessage(QString message) {
    QJsonDocument doc = QJsonDocument::fromJson(message.toUtf8());
    if (doc.isNull() || !doc.isObject()) return;

    QJsonObject obj = doc.object();
    QString type = obj["type"].toString();

    // 1. ESP32 Gửi: Nhấn nút chọn số (T, U, V, W, X, Y)
    // Cú pháp JSON mong đợi: {"type": "PAD_SELECT", "label": "T"}
    if (type == "PAD_SELECT") {
        QString label = obj["label"].toString();
        m_board->selectTargetDigit(label);
    }

    // 2. ESP32 Gửi: Nhấn nét vẽ trên Drawing Pad (0 đến 6)
    // Cú pháp JSON mong đợi: {"type": "PAD_DRAW", "segIdx": 2}
    else if (type == "PAD_DRAW") {
        int segIdx = obj["segIdx"].toInt();
        m_board->tapDrawingPad(segIdx);
    }

    // 3. ESP32 Gửi: Nhấn các nút hỏi đáp (Q1-Q4, hoặc A-S)
    // Cú pháp JSON mong đợi: {"type": "ACTION", "btnId": "BTN_Q1"}
    else if (type == "ACTION") {
        QString btnId = obj["btnId"].toString();
        m_board->handleButtonPress("HW", btnId);
    }
}

void HardwareServer::socketDisconnected() {
    QWebSocket *client = qobject_cast<QWebSocket *>(sender());
    if (client) {
        m_clients.removeAll(client);
        client->deleteLater();
        qDebug() << "[NET] ESP32 Disconnected";
        emit connectedChanged();
    }
}

void HardwareServer::sendToHardware(const QJsonObject& json) {
    QJsonDocument doc(json);
    QString message = doc.toJson(QJsonDocument::Compact);
    for (QWebSocket *client : std::as_const(m_clients)) {
        client->sendTextMessage(message);
    }
}

// --- GỬI LỆNH XUỐNG ESP32: Cập nhật vạch LED ---
void HardwareServer::onSegStateUpdated(int ledIdx, QVariantList state) {
    // Không cần check điều kiện vùng, có vạch nào thay đổi là báo xuống ESP32
    for (int i = 0; i < 7; i++) {
        QJsonObject obj;
        obj["type"] = "DRAW";
        obj["ledIdx"] = ledIdx;
        obj["segIdx"] = i;
        obj["val"] = state[i].toInt();
        sendToHardware(obj);
    }
}

// --- GỬI LỆNH XUỐNG ESP32: Cập nhật màn hình OLED ---
void HardwareServer::onOledUpdateRequested(QString line1, QString line2) {
    // Lưu lại nội dung cuối để "chép bài" cho client reconnect (xem onNewConnection)
    m_lastOledLine1 = line1;
    m_lastOledLine2 = line2;

    QJsonObject obj;
    obj["type"] = "OLED";

    // Nếu GameBoard yêu cầu đưa OLED về mặc định
    if (line2 == "DEFAULT_LAYOUT") {
        obj["layout"] = "default"; // Báo cho ESP32 tự dựng lại layout Time/Point
    }
    // Nếu GameBoard yêu cầu in nội dung cụ thể
    else {
        obj["layout"] = "text";
        obj["line1"] = line1;
        obj["line2"] = line2;
    }

    qDebug() << "[NET] Gửi OLED:" << line1 << "|" << line2;
    sendToHardware(obj);
}