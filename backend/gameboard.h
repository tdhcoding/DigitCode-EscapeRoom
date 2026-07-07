#pragma once
#include <QObject>
#include <QVariantList>
#include <QVariantMap>
#include <QPair>
#include <QTimer>
#include <QSet>
#include <QString>

class GameBoard : public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList segStates READ segStates NOTIFY segStatesChanged)
    Q_PROPERTY(int points READ points NOTIFY pointsChanged)
    Q_PROPERTY(int activeDigit READ activeDigit NOTIFY activeDigitChanged)
    Q_PROPERTY(int playTimeSeconds READ playTimeSeconds NOTIFY playTimeSecondsChanged)

public:
    // Máy Trạng Thái (State Machine) quản lý 4 câu hỏi
    enum GameState {
        DEFAULT,
        WAIT_Q1,
        WAIT_Q2_1, WAIT_Q2_2,
        WAIT_Q3,
        WAIT_Q4_1, WAIT_Q4_2
    };
    Q_ENUM(GameState)

    explicit GameBoard(QObject* parent = nullptr);

    QVariantList segStates() const { return m_segStates; }
    int points() const { return m_points; }
    int activeDigit() const { return m_activeDigit; }
    int playTimeSeconds() const { return m_playTimeSeconds; }

    // --- 1. DÀNH CHO GIAO DIỆN PHẦN MỀM UI (QML CLICK CHUỘT) ---
    Q_INVOKABLE void tapSegment(int ledIdx, int segIdx);
    Q_INVOKABLE void holdSegment(int ledIdx, int segIdx);
    Q_INVOKABLE void setLedDigit(int ledIdx, int digit);
    Q_INVOKABLE void setLedSegState(int ledIdx, const QVariantList& state);

    // --- 2. DÀNH CHO PHẦN CỨNG DRAWING PAD ---
    Q_INVOKABLE void selectTargetDigit(const QString& label); // Bấm nút chọn số (T-Y)
    Q_INVOKABLE void tapDrawingPad(int segIdx);               // Bấm nút vạch ở góc máy

    // --- 3. CỔNG GIAO TIẾP GƯƠNG 2 CHIỀU (XỬ LÝ LUẬT GAME) ---
    Q_INVOKABLE void handleButtonPress(const QString& source, const QString& btnId);

    Q_INVOKABLE void pauseGame();
    Q_INVOKABLE void resumeGame();
    Q_INVOKABLE void verifyCode(const QString& guessCode);

    // Các hàm hệ thống
    Q_INVOKABLE void generateRandomPuzzle();
    Q_INVOKABLE QVariantList getSegState(int ledIdx) const;
    void updateSeg(int ledIdx, int segIdx, int val);

signals:
    void segStatesChanged();
    void segStateUpdated(int ledIdx, QVariantList state);
    void topStatsChanged(QVariantMap stats);

    // Tín hiệu mới cho V4
    void pointsChanged();
    void activeDigitChanged();
    void oledUpdateRequested(QString line1, QString line2);

    // Tín hiệu báo cho QML biết có manh mối mới được "mua" thành công
    void clueRevealed(QString clueType, QString targetId, QVariant value);

    // Tín hiệu báo cho QML biết đã tạo đề mới, yêu cầu xóa sạch các manh mối cũ trên màn hình
    void puzzleGenerated();

    void playTimeSecondsChanged();
    void gameWon();
    void gameLost();
    void wrongGuessWarning();

private slots:
    void onPenaltyTimeout(); // Hàm gọi khi quá 10s chần chừ
    void onGlobalTimerTick(); // Hàm gọi mỗi 1 giây để đếm thời gian chơi
    void onOledClearTimeout(); // Hàm xử lý xóa màn hình OLED sau 3s

private:
    QVariantList m_segStates;
    QVariantMap  m_backups;
    QString m_secretCode;
    // --- BIẾN LƯU TRỮ ĐÁP ÁN (Dùng để đối chiếu khi hỏi) ---
    QVariantList m_ansEvenOdd;
    QVariantList m_ansHCmp;
    QVariantList m_ansVCmp;
    QVariantList m_ansColCounts;
    QVariantList m_ansRowCounts;

    // --- CÁC HÀM HELPER XỬ LÝ LOGIC SẠCH (Clean Code) ---
    void processQ1(const QString& btnId);
    void processQ2(const QString& btnId);
    void processQ3(const QString& btnId);
    void processQ4(const QString& btnId);
    void processReview(const QString& btnId);
    void lockAndLightUpFull(const QString& btnId);
    void checkWinCondition();

    // Hàm phụ trợ
    bool isAdjacent(const QString& btn1, const QString& btn2);
    int getMaxLed(const QString& btnId);
    void revealClueToUI(const QString& type, const QString& id, const QVariant& value);

    // --- BIẾN QUẢN LÝ LUẬT CHƠI (V4) ---
    int m_points;
    int m_activeDigit;
    GameState m_currentState;
    QTimer* m_penaltyTimer;   // Đồng hồ cát 10s (Sẽ stop khi người chơi trả lời kịp)
    QTimer* m_globalTimer;    // Đồng hồ tổng (Không bao giờ stop)
    QTimer* m_oledClearTimer;
    int m_playTimeSeconds;    // Lưu tổng số giây đã chơi thực tế
    int m_guessCount;         // Đếm số lần đoán sai

    // --- BIẾN LƯU VẾT & CHỐNG TRÙNG LẶP ---
    QString m_tempTarget1;
    QSet<QString> m_askedQ1;
    QSet<QString> m_askedQ2;
    QSet<QString> m_askedQ3;
    QSet<QString> m_askedQ4;
    QSet<QString> m_lockedFull;
    QSet<QString> m_lockedSegments;
};