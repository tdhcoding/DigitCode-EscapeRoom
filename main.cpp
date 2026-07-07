#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "backend/gameboard.h"
#include "backend/hardwareserver.h" // Nhúng thư viện Server

int main(int argc, char *argv[])
{
    qputenv("QT_QUICK_CONTROLS_STYLE", "Basic");

    QGuiApplication app(argc, argv);
    QQmlApplicationEngine engine;

    // Tạo backend và expose sang QML
    GameBoard board;
    engine.rootContext()->setContextProperty("gameBoard", &board);

    // BẬT SERVER MẠNG VÀ TRUYỀN CON TRỞ BOARD VÀO
    HardwareServer hwServer(&board);

    QObject::connect(
        &engine,
        &QQmlApplicationEngine::objectCreationFailed,
        &app,
        []() { QCoreApplication::exit(-1); },
        Qt::QueuedConnection);

    engine.loadFromModule("DigitCode_SINGLE", "Main");
    return app.exec();
}