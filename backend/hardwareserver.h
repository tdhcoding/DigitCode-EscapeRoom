#ifndef HARDWARESERVER_H
#define HARDWARESERVER_H

#include <QObject>
#include <QWebSocketServer>
#include <QWebSocket>
#include <QJsonDocument>
#include <QJsonObject>
#include "gameboard.h"

class HardwareServer : public QObject
{
    Q_OBJECT
    // Cho màn hình "Play in Real-life" biết trạng thái kết nối + IP để đối chiếu secrets.h
    Q_PROPERTY(bool connected READ connected NOTIFY connectedChanged)
    Q_PROPERTY(QString serverAddress READ serverAddress CONSTANT)
public:
    explicit HardwareServer(GameBoard* board, QObject *parent = nullptr);
    ~HardwareServer();

    bool connected() const { return !m_clients.isEmpty(); }
    QString serverAddress() const;

    // Hàm gọi để gửi lệnh từ Qt xuống thẳng ESP32
    void sendToHardware(const QJsonObject& json);

signals:
    void connectedChanged();

private slots:
    void onNewConnection();
    void processTextMessage(QString message);
    void socketDisconnected();

    // Hứng tín hiệu Gameboard (Từ C++ gửi xuống ESP32)
    void onSegStateUpdated(int ledIdx, QVariantList state);
    void onOledUpdateRequested(QString line1, QString line2); // MỚI: Nhận lệnh in OLED
    void onStatsChanged(); // Đẩy thời gian/điểm xuống OLED thật (gói STATS)

private:
    QWebSocketServer *m_server;
    QList<QWebSocket *> m_clients;
    GameBoard* m_board;
    // Nội dung OLED cuối cùng - dùng để đồng bộ lại cho ESP32 reconnect giữa ván
    QString m_lastOledLine1;
    QString m_lastOledLine2;
};

#endif // HARDWARESERVER_H