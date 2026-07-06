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
public:
    explicit HardwareServer(GameBoard* board, QObject *parent = nullptr);
    ~HardwareServer();

    // Hàm gọi để gửi lệnh từ Qt xuống thẳng ESP32
    void sendToHardware(const QJsonObject& json);

private slots:
    void onNewConnection();
    void processTextMessage(QString message);
    void socketDisconnected();

    // Hứng tín hiệu Gameboard (Từ C++ gửi xuống ESP32)
    void onSegStateUpdated(int ledIdx, QVariantList state);
    void onOledUpdateRequested(QString line1, QString line2); // MỚI: Nhận lệnh in OLED

private:
    QWebSocketServer *m_server;
    QList<QWebSocket *> m_clients;
    GameBoard* m_board;
};

#endif // HARDWARESERVER_H