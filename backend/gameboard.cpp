#include "gameboard.h"
#include <QDebug>
#include <QRandomGenerator>

static const QMap<QString, int> SEG_MAP = {
    {"a",0},{"b",1},{"c",2},{"d",3},{"e",4},{"f",5},{"g",6}
};
static const QMap<QString, QStringList> COL_GROUPS = {
    {"0", {"f","e"}}, {"1", {"a","g","d"}}, {"2", {"b","c"}}
};
static const QMap<QString, QStringList> ROW_GROUPS = {
    {"0", {"a"}}, {"1", {"f","b"}}, {"2", {"g"}}, {"3", {"e","c"}}, {"4", {"d"}}
};
static const QMap<QString, QPair<int,int>> COL_LED_MAP = {
    {"A", {0,3}}, {"B", {0,3}}, {"C", {0,3}},
    {"D", {1,4}}, {"E", {1,4}}, {"F", {1,4}},
    {"G", {2,5}}, {"H", {2,5}}, {"I", {2,5}}
};
static const QMap<QString, int> COL_IDX_MAP = {
    {"A",0}, {"B",1}, {"C",2}, {"D",0}, {"E",1}, {"F",2}, {"G",0}, {"H",1}, {"I",2}
};
static const QMap<QChar, QVariantList> DIGIT_MAP = {
    {'0', {1,1,1,1,1,1,0}}, {'1', {0,1,1,0,0,0,0}}, {'2', {1,1,0,1,1,0,1}},
    {'3', {1,1,1,1,0,0,1}}, {'4', {0,1,1,0,0,1,1}}, {'5', {1,0,1,1,0,1,1}},
    {'6', {1,0,1,1,1,1,1}}, {'7', {1,1,1,0,0,0,0}}, {'8', {1,1,1,1,1,1,1}},
    {'9', {1,1,1,1,0,1,1}}
};

GameBoard::GameBoard(QObject* parent) : QObject(parent),
    m_points(100),
    m_activeDigit(-1),
    m_currentState(DEFAULT),
    m_playTimeSeconds(0)
{
    // SINGLE Mode: Quản lý 6 LED (0 đến 5)
    for (int i = 0; i < 6; i++) {
        m_segStates.append(QVariantList({0,0,0,0,0,0,0}));
    }

    // 1. Khởi tạo Đồng hồ phạt 10s (Chỉ chạy 1 lần khi được gọi)
    m_penaltyTimer = new QTimer(this);
    m_penaltyTimer->setSingleShot(true);
    connect(m_penaltyTimer, &QTimer::timeout, this, &GameBoard::onPenaltyTimeout);

    // 2. Khởi tạo Đồng hồ tổng (Chạy lặp đi lặp lại không ngừng)
    m_globalTimer = new QTimer(this);
    connect(m_globalTimer, &QTimer::timeout, this, &GameBoard::onGlobalTimerTick);

    // 3. Khởi tạo Đồng hồ dọn dẹp OLED 3 giây
    m_oledClearTimer = new QTimer(this);
    m_oledClearTimer->setSingleShot(true);
    connect(m_oledClearTimer, &QTimer::timeout, this, &GameBoard::onOledClearTimeout);
}

void GameBoard::onOledClearTimeout() {
    // Chỉ xóa nếu người chơi đang không ở trạng thái chọn câu hỏi dở dang
    if (m_currentState == DEFAULT) {
        emit oledUpdateRequested("", "DEFAULT_LAYOUT");
    }
}

// Logic nhận diện Phá đảo (Win Condition)
void GameBoard::checkWinCondition() {
    if (m_secretCode.isEmpty()) return;

    bool won = true;
    for (int i = 0; i < 6; i++) {
        QVariantList currentState = m_segStates[i].toList();
        QVariantList targetState = DIGIT_MAP[m_secretCode[i]].toList();
        if (currentState != targetState) {
            won = false;
            break;
        }
    }

    if (won) {
        // Dừng toàn bộ đồng hồ
        m_globalTimer->stop();
        if (m_penaltyTimer->isActive()) m_penaltyTimer->stop();
        if (m_oledClearTimer->isActive()) m_oledClearTimer->stop();

        m_secretCode = ""; // Xóa mã để chặn hàm chạy nhiều lần

        // Tính toán chuỗi thời gian hiển thị
        int m = m_playTimeSeconds / 60;
        int s = m_playTimeSeconds % 60;
        QString timeStr = QString("%1:%2").arg(m, 2, 10, QChar('0')).arg(s, 2, 10, QChar('0'));

        emit oledUpdateRequested("YOU ESCAPED!", "Clear time: " + timeStr);
        emit gameWon(); // Báo cho QML hiện lại nút
    }
}

void GameBoard::onGlobalTimerTick() {
    m_playTimeSeconds++; // Tăng thời gian chơi thực tế lên 1 giây
    emit playTimeSecondsChanged();

    // Logic trừ điểm thụ động: Cứ đúng 60 giây trôi qua thì trừ 1 điểm
    if (m_playTimeSeconds > 0 && m_playTimeSeconds % 60 == 0) {
        // Có thể thêm điều kiện chặn không cho điểm âm nếu bạn muốn: if (m_points > 0)
        m_points -= 1;
        emit pointsChanged(); // Báo cho giao diện QML và OLED cập nhật ngay lập tức
    }

    // LOGIC GAME OVER: Chết khi cạn điểm
    if (m_points <= 0) {
        m_points = 0; // Tránh điểm âm
        emit pointsChanged();

        m_globalTimer->stop();
        if (m_penaltyTimer->isActive()) m_penaltyTimer->stop();
        if (m_oledClearTimer->isActive()) m_oledClearTimer->stop();

        emit oledUpdateRequested("YOU DIED...", "Better luck next life");
        emit gameLost(); // Bắn tín hiệu sang QML
    }
}

// --- LOGIC PHẠT TIMER 5 GIÂY ---
void GameBoard::onPenaltyTimeout() {
    m_points -= 1;
    emit pointsChanged();

    // LOGIC GAME OVER TRONG LÚC BỊ PHẠT
    if (m_points <= 0) {
        m_points = 0;
        emit pointsChanged();
        m_globalTimer->stop();
        emit oledUpdateRequested("YOU DIED...", "Better luck next life");
        emit gameLost();
        return; // Kết thúc hàm luôn, không chạy đoạn set trạng thái DEFAULT ở dưới nữa
    }

    emit oledUpdateRequested("Playing with me?", "-1 Point");
    m_oledClearTimer->start(3000);

    m_currentState = DEFAULT;
    m_tempTarget1.clear();
}

// --- LOGIC DRAWING PAD ---
void GameBoard::selectTargetDigit(const QString& label) {
    QStringList digits = {"T", "U", "V", "W", "X", "Y"};
    int idx = digits.indexOf(label);

    if (idx != -1) {
        m_activeDigit = idx;
        emit activeDigitChanged();
    }
}

void GameBoard::tapDrawingPad(int segIdx) {
    if (m_activeDigit != -1) {
        tapSegment(m_activeDigit, segIdx);
    }
}

//Step2 ---- handleButtonPress
void GameBoard::handleButtonPress(const QString& source, const QString& btnId) {
    // 0. Các nút chỉ dành cho phần cứng (VERIFY vẽ trên sa bàn, NEW GAME vật lý) —
    // hoạt động bất kể m_currentState đang là gì, giống BTN_Q1-4.
    // BTN_NEWGAME chỉ được firmware gửi sau khi giữ nút 5 giây (chống bấm nhầm).
    if (btnId == "BTN_NEWGAME") {
        generateRandomPuzzle();
        return;
    }

    // Nút vật lý bấm được mọi lúc (khác nút QML bị ẩn theo màn hình): nếu chưa
    // từng sinh ván nào thì các bảng đáp án còn rỗng, xử lý tiếp sẽ truy cập
    // index ngoài biên -> crash. Chặn tất cả trừ BTN_NEWGAME ở trên.
    if (m_ansEvenOdd.isEmpty()) {
        emit oledUpdateRequested("No game running", "Hold NEW GAME 5s");
        m_oledClearTimer->start(3000);
        return;
    }

    if (btnId == "BTN_VERIFY") {
        // Không còn ván đang chạy (chưa bắt đầu / đã thắng-thua xong): từ chối,
        // nếu không mọi mã đoán đều "sai" so với m_secretCode rỗng -> strike oan.
        if (m_secretCode.isEmpty()) {
            emit oledUpdateRequested("No active game", "Hold NEW GAME 5s");
            m_oledClearTimer->start(3000);
            return;
        }

        QString guess;
        bool valid = true;
        for (int i = 0; i < 6; i++) {
            int digit = decodeDigitFromSegments(getSegState(i));
            if (digit == -1) { valid = false; break; }
            guess += QString::number(digit);
        }

        if (valid) {
            verifyCode(guess);
        } else {
            emit oledUpdateRequested("INVALID CODE", "Draw digit 0-9 first");
            m_oledClearTimer->start(3000);
        }
        return;
    }

    // 1. Cho phép "bẻ lái" sang câu hỏi khác bất cứ lúc nào (Override)
    if (btnId == "BTN_Q1" || btnId == "BTN_Q2" || btnId == "BTN_Q3" || btnId == "BTN_Q4") {

        m_oledClearTimer->stop();

        m_tempTarget1.clear(); // Xóa bộ nhớ tạm nếu đang chọn dở câu 2, câu 4

        if (btnId == "BTN_Q1") {
            m_currentState = WAIT_Q1;
            emit oledUpdateRequested("Q1: Pick one...", "");
        } else if (btnId == "BTN_Q2") {
            m_currentState = WAIT_Q2_1;
            emit oledUpdateRequested("Q2: Pick two...", "");
        } else if (btnId == "BTN_Q3") {
            m_currentState = WAIT_Q3;
            emit oledUpdateRequested("Q3: Pick a row/column...", "");
        } else if (btnId == "BTN_Q4") {
            m_currentState = WAIT_Q4_1;
            emit oledUpdateRequested("Q4: Pick a row/column...", "");
        }

        m_penaltyTimer->start(10000); // Khởi động/Reset lại đồng hồ 10s
        return; // Xử lý xong thì dừng luôn, chờ người chơi bấm tiếp
    }

    // 2. Chế độ Review Mode (Chỉ chạy khi đang rảnh rỗi)
    if (m_currentState == DEFAULT) {
        if (btnId >= "A" && btnId <= "S") {
            processReview(btnId);
        } else if (btnId >= "T" && btnId <= "Y") {
            processReviewTarget(btnId); // xem lại Q1 (và Q2 nếu bấm 2 nút liền kề liên tiếp)
        }
        return;
    }

    // 3. Phân luồng xử lý theo trạng thái đang chờ (WAIT)
    switch (m_currentState) {
    case WAIT_Q1:           processQ1(btnId); break;
    case WAIT_Q2_1:
    case WAIT_Q2_2:         processQ2(btnId); break;
    case WAIT_Q3:           processQ3(btnId); break;
    case WAIT_Q4_1:
    case WAIT_Q4_2:         processQ4(btnId); break;
    default: break;
    }
}

void GameBoard::processQ1(const QString& btnId) {
    // Ràng buộc input
    if (btnId < "T" || btnId > "Y") return;

    // Kiểm tra trùng lặp
    if (m_askedQ1.contains(btnId)) {
        emit oledUpdateRequested("Forget? Find it in ur mind", "Or in my mind I guess...");
        m_oledClearTimer->start(3000); // nhánh duy nhất từng thiếu dòng này -> OLED treo message vĩnh viễn
        m_currentState = DEFAULT;
        m_penaltyTimer->stop();
        return;
    }

    // Hợp lệ
    m_penaltyTimer->stop();
    m_askedQ1.insert(btnId);
    m_points -= 5;
    emit pointsChanged();

    // In đáp án thật lên OLED (0 = chẵn, 1 = lẻ) — người chơi thuần phần cứng
    // không thấy được chấm EODot bên QML nên OLED phải mang đủ thông tin.
    int index = QString("TUVWXYZ").indexOf(btnId);
    bool isOdd = m_ansEvenOdd[index].toInt() == 1;
    emit oledUpdateRequested(QString("%1: %2").arg(btnId, isOdd ? "ODD (.)" : "EVEN (..)"), "");

    // Gửi tín hiệu sang QML để bật đèn EODot
    revealClueToUI("Q1_EODOT", btnId, m_ansEvenOdd[index]);

    m_oledClearTimer->start(3000);
    m_currentState = DEFAULT;
}

void GameBoard::processQ2(const QString& btnId) {
    if (btnId < "T" || btnId > "Y") return;

    if (m_currentState == WAIT_Q2_1) {
        m_tempTarget1 = btnId;
        m_currentState = WAIT_Q2_2;
        emit oledUpdateRequested("Q2: Another one...", "");
        return;
    }

    if (m_currentState == WAIT_Q2_2) {
        if (!isAdjacent(m_tempTarget1, btnId)) {
            emit oledUpdateRequested("INVALID, pick again...", "");
            return;
        }

        // Sắp xếp alphabetical để chống trùng lặp chiều ngược (V-U = U-V)
        QString pair = (m_tempTarget1 < btnId) ? (m_tempTarget1 + "-" + btnId) : (btnId + "-" + m_tempTarget1);

        if (m_askedQ2.contains(pair)) {
            emit oledUpdateRequested("Forget? Find it in ur mind", "Or in my mind I guess...");
            m_oledClearTimer->start(3000);
            m_currentState = DEFAULT;
            m_penaltyTimer->stop();
            return;
        }

        m_penaltyTimer->stop();
        m_askedQ2.insert(pair);
        m_points -= 5;
        emit pointsChanged();

        int val = cmpValueForPair(pair);

        // In đáp án thật lên OLED — người chơi thuần phần cứng không thấy
        // được mũi tên CmpArrow bên QML nên OLED phải mang đủ thông tin.
        QString rel = val > 0 ? ">" : (val < 0 ? "<" : "=");
        emit oledUpdateRequested(QString("%1 %2 %3").arg(pair.left(1), rel, pair.right(1)), "");

        revealClueToUI("Q2_ARROW", pair, val);

        m_oledClearTimer->start(3000);
        m_currentState = DEFAULT;
    }
}

void GameBoard::processQ3(const QString& btnId) {
    if (btnId < "A" || btnId > "S") return;

    if (m_askedQ3.contains(btnId) || m_lockedFull.contains(btnId)) {
        emit oledUpdateRequested("Forget? Find it in ur mind", "Or in my mind I guess...");
        m_oledClearTimer->start(3000);
        m_currentState = DEFAULT;
        m_penaltyTimer->stop();
        return;
    }

    m_penaltyTimer->stop();
    m_askedQ3.insert(btnId);
    m_points -= 5;
    emit pointsChanged();

    // Lấy đáp án thực tế
    int index = (btnId <= "I") ? (btnId.at(0).unicode() - 'A') : (btnId.at(0).unicode() - 'J');
    int count = (btnId <= "I") ? m_ansColCounts[index].toInt() : m_ansRowCounts[index].toInt();

    // Khóa luôn nếu count chạm Max LED
    if (count == getMaxLed(btnId)) {
        m_lockedFull.insert(btnId);
        lockAndLightUpFull(btnId);
    }

    // Phản hồi OLED
    QString msg = QString("%1 has %2 demon(s)").arg(btnId).arg(count);
    emit oledUpdateRequested(msg, "");

    // Cập nhật QML
    revealClueToUI("Q3_COUNTER", btnId, count);

    m_oledClearTimer->start(3000);
    m_currentState = DEFAULT;
}

bool GameBoard::isAdjacent(const QString& btn1, const QString& btn2) {
    // Các cặp nằm ngang
    QSet<QString> hPairs = {"T-U", "U-V", "W-X", "X-Y", "U-T", "V-U", "X-W", "Y-X"};
    // Các cặp nằm dọc
    QSet<QString> vPairs = {"T-W", "W-T", "U-X", "X-U", "V-Y", "Y-V"};

    QString pair = btn1 + "-" + btn2;
    return hPairs.contains(pair) || vPairs.contains(pair);
}

int GameBoard::getMaxLed(const QString& btnId) {
    // Tính max_LED. Ví dụ: cột A có 2 vạch (f, e) x 2 hàng LED (trên, dưới) = 4
    if (btnId == "A" || btnId == "D" || btnId == "G") return 4; // f, e
    if (btnId == "B" || btnId == "E" || btnId == "H") return 6; // a, g, d
    if (btnId == "C" || btnId == "F" || btnId == "I") return 4; // b, c

    if (btnId == "J" || btnId == "O") return 3; // a
    if (btnId == "K" || btnId == "P") return 6; // f, b
    if (btnId == "L" || btnId == "Q") return 3; // g
    if (btnId == "M" || btnId == "R") return 6; // e, c
    if (btnId == "N" || btnId == "S") return 3; // d

    return 0;
}

// Hàm tự động bật LED và gọi nó ở Q3, Q4:
void GameBoard::lockAndLightUpFull(const QString& btnId) {
    QList<QPair<int, int>> targets;

    // Tìm các vạch LED thuộc Cột A-I
    if (btnId >= "A" && btnId <= "I") {
        if (!COL_LED_MAP.contains(btnId)) return;
        auto [ledTop, ledBot] = COL_LED_MAP[btnId];
        int colIdx = COL_IDX_MAP[btnId];
        const QStringList segs = COL_GROUPS[QString::number(colIdx)];
        for (const QString& s : segs) {
            int sIdx = SEG_MAP.value(s, -1);
            if (sIdx != -1) { targets.append({ledTop, sIdx}); targets.append({ledBot, sIdx}); }
        }
    }
    // Tìm các vạch LED thuộc Hàng J-S
    else if (btnId >= "J" && btnId <= "S") {
        bool isRow2 = (btnId >= "O");
        const QStringList names1 = {"J","K","L","M","N"};
        const QStringList names2 = {"O","P","Q","R","S"};
        int rowIdx = isRow2 ? names2.indexOf(btnId) : names1.indexOf(btnId);
        if (rowIdx == -1) return;
        const QStringList segs = ROW_GROUPS[QString::number(rowIdx)];
        int offset = isRow2 ? 3 : 0;
        for (int i = 0; i < 3; i++) {
            for (const QString& s : segs) {
                int sIdx = SEG_MAP.value(s, -1);
                if (sIdx != -1) targets.append({offset + i, sIdx});
            }
        }
    }

    // Bật sáng và khóa vĩnh viễn các vạch đã tìm được
    for (auto target : targets) {
        int lIdx = target.first;
        int sIdx = target.second;

        m_lockedSegments.insert(QString("%1-%2").arg(lIdx).arg(sIdx)); // Khóa lại

        QVariantList led = getSegState(lIdx);
        led[sIdx] = 1; // Bật sáng
        m_segStates[lIdx] = led;

        emit segStatesChanged();
        emit segStateUpdated(lIdx, led);
    }
}

//Step3 ---- generateRandomPuzzle and revealClueToUI

void GameBoard::generateRandomPuzzle() {
    // 1. DỌN DẸP TRẠNG THÁI HỆ THỐNG KHI TẠO ĐỀ MỚI
    m_guessCount = 0;
    m_playTimeSeconds = 0;
    emit playTimeSecondsChanged();
    m_points = 100;
    emit pointsChanged();

    m_currentState = DEFAULT;
    m_tempTarget1.clear();
    m_lastReviewTarget.clear();
    m_askedQ1.clear();
    m_askedQ2.clear();
    m_askedQ3.clear();
    m_askedQ4.clear();
    m_lockedFull.clear();
    m_lockedSegments.clear();

    for (int i = 0; i < 6; i++) {
        m_segStates[i] = QVariantList({0, 0, 0, 0, 0, 0, 0});
        emit segStateUpdated(i, m_segStates[i].toList()); // Báo xuống ESP32
    }
    emit segStatesChanged(); // Báo cho QML cập nhật UI

    if (m_penaltyTimer->isActive()) m_penaltyTimer->stop();

    m_globalTimer->start(1000);

    emit oledUpdateRequested("Time: [mm:ss]", "Points: 100\nDeath is waiting...");

    // 2. SINH MÃ BÍ MẬT (Giữ nguyên luật Sudoku của V3)
    QString code = "";
    while (code.length() < 6) {
        int currentLength = code.length();
        int randDigit = QRandomGenerator::global()->bounded(10);
        QString ch = QString::number(randDigit);

        if (code.count(ch) >= 2) continue;
        if (currentLength % 3 != 0 && code.at(currentLength - 1) == ch.at(0)) continue;
        if (currentLength >= 3 && code.at(currentLength - 3) == ch.at(0)) continue;
        code += ch;
    }
    m_secretCode = code;
    qDebug() << "[PUZZLE GENERATOR] New Secret Code:" << m_secretCode;

    // 3. TÍNH TOÁN VÀ "GIẤU" ĐÁP ÁN VÀO BIẾN NỘI BỘ
    QList<QVariantList> st;
    for (int i = 0; i < 6; i++) {
        st.append(DIGIT_MAP[m_secretCode[i]]);
    }

    // A. Lưu trạng thái Chẵn/Lẻ (Q1)
    m_ansEvenOdd.clear();
    for (int i = 0; i < 6; i++) {
        m_ansEvenOdd.append(m_secretCode[i].digitValue() % 2 == 0 ? 0 : 1);
    }

    // B. Lưu trạng thái So sánh Ngang & Dọc (Q2)
    auto cmp = [](int a, int b) -> int { return a > b ? 1 : a < b ? -1 : 0; };

    m_ansHCmp.clear();
    m_ansHCmp.append(cmp(m_secretCode[0].digitValue(), m_secretCode[1].digitValue()));
    m_ansHCmp.append(cmp(m_secretCode[1].digitValue(), m_secretCode[2].digitValue()));
    m_ansHCmp.append(cmp(m_secretCode[3].digitValue(), m_secretCode[4].digitValue()));
    m_ansHCmp.append(cmp(m_secretCode[4].digitValue(), m_secretCode[5].digitValue()));

    m_ansVCmp.clear();
    m_ansVCmp.append(cmp(m_secretCode[0].digitValue(), m_secretCode[3].digitValue()));
    m_ansVCmp.append(cmp(m_secretCode[1].digitValue(), m_secretCode[4].digitValue()));
    m_ansVCmp.append(cmp(m_secretCode[2].digitValue(), m_secretCode[5].digitValue()));

    // C. Lưu số lượng LED đếm được theo Cột và Hàng (Q3 & Q4)
    auto countSegs = [&](int ledTop, int ledBot, QStringList segs) -> int {
        int count = 0;
        for (const QString& s : segs) {
            int idx = SEG_MAP.value(s, -1);
            if (idx >= 0) {
                count += st[ledTop][idx].toInt() > 0 ? 1 : 0;
                count += st[ledBot][idx].toInt() > 0 ? 1 : 0;
            }
        }
        return count;
    };

    m_ansColCounts.clear();
    m_ansColCounts.append(countSegs(0, 3, {"f","e"}));     // A
    m_ansColCounts.append(countSegs(0, 3, {"a","g","d"})); // B
    m_ansColCounts.append(countSegs(0, 3, {"b","c"}));     // C
    m_ansColCounts.append(countSegs(1, 4, {"f","e"}));     // D
    m_ansColCounts.append(countSegs(1, 4, {"a","g","d"})); // E
    m_ansColCounts.append(countSegs(1, 4, {"b","c"}));     // F
    m_ansColCounts.append(countSegs(2, 5, {"f","e"}));     // G
    m_ansColCounts.append(countSegs(2, 5, {"a","g","d"})); // H
    m_ansColCounts.append(countSegs(2, 5, {"b","c"}));     // I

    auto countRow = [&](QList<int> leds, QStringList segs) -> int {
        int count = 0;
        for (int led : leds) {
            for (const QString& s : segs) {
                int idx = SEG_MAP.value(s, -1);
                if (idx >= 0) count += st[led][idx].toInt() > 0 ? 1 : 0;
            }
        }
        return count;
    };

    m_ansRowCounts.clear();
    m_ansRowCounts.append(countRow({0,1,2}, {"a"}));     // J
    m_ansRowCounts.append(countRow({0,1,2}, {"f","b"})); // K
    m_ansRowCounts.append(countRow({0,1,2}, {"g"}));     // L
    m_ansRowCounts.append(countRow({0,1,2}, {"e","c"})); // M
    m_ansRowCounts.append(countRow({0,1,2}, {"d"}));     // N
    m_ansRowCounts.append(countRow({3,4,5}, {"a"}));     // O
    m_ansRowCounts.append(countRow({3,4,5}, {"f","b"})); // P
    m_ansRowCounts.append(countRow({3,4,5}, {"g"}));     // Q
    m_ansRowCounts.append(countRow({3,4,5}, {"e","c"})); // R
    m_ansRowCounts.append(countRow({3,4,5}, {"d"}));     // S

    // 4. BÁO CHO QML BIẾT ĐÃ CÓ ĐỀ MỚI ĐỂ LÀM TRỐNG GIAO DIỆN
    emit puzzleGenerated();
}

int GameBoard::decodeDigitFromSegments(const QVariantList& segs) const {
    if (segs.size() != 7) return -1;

    // Chuẩn hóa: coi mọi giá trị khác 0 (kể cả trạng thái "hold"=2) là sáng,
    // vì DIGIT_MAP chỉ mô tả mẫu 0/1.
    QVariantList normalized;
    for (const QVariant& v : segs) {
        normalized.append(v.toInt() != 0 ? 1 : 0);
    }

    for (auto it = DIGIT_MAP.constBegin(); it != DIGIT_MAP.constEnd(); ++it) {
        if (it.value().toList() == normalized) {
            return it.key().digitValue();
        }
    }
    return -1;
}

void GameBoard::revealClueToUI(const QString& type, const QString& id, const QVariant& value) {
    // In ra console để debug xem C++ có bắn đúng không
    qDebug() << "[REVEAL CLUE] Type:" << type << "| Target:" << id << "| Value:" << value;

    // Bắn tín hiệu sang QML
    emit clueRevealed(type, id, value);
}

//Step4 ---- Q4 và Review Mode
void GameBoard::processQ4(const QString& btnId) {
    if (btnId < "A" || btnId > "S") return;

    if (m_currentState == WAIT_Q4_1) {
        m_tempTarget1 = btnId;
        m_currentState = WAIT_Q4_2;
        emit oledUpdateRequested("Q4: Pick another row/column...", "");
        return;
    }

    if (m_currentState == WAIT_Q4_2) {
        // Ràng buộc: Nút thứ 2 phải khác nút thứ 1
        if (btnId == m_tempTarget1) {
            emit oledUpdateRequested("INVALID, pick again...", "");
            return; // Giữ nguyên timer, bắt chọn lại
        }

        // Kiểm tra điều kiện khóa/trùng cho cả 2 nút
        bool btn1_locked = m_askedQ3.contains(m_tempTarget1) || m_lockedFull.contains(m_tempTarget1);
        bool btn2_locked = m_askedQ3.contains(btnId) || m_lockedFull.contains(btnId);

        if (btn1_locked || btn2_locked) {
            emit oledUpdateRequested("Forget? Find it in ur mind", "Or in my mind I guess...");
            m_oledClearTimer->start(3000);
            m_currentState = DEFAULT;
            m_penaltyTimer->stop();
            return;
        }

        // Hợp lệ -> Dừng timer, trừ điểm
        m_penaltyTimer->stop();
        m_points -= 5;
        emit pointsChanged();

        // Lambda function nội bộ để kiểm tra từng nút cho gọn code
        auto checkNode = [&](const QString& node) -> QString {
            m_askedQ4.insert(node); // Đánh dấu là đã hỏi Q4

            // Lấy số lượng quỷ thực tế
            int index = (node <= "I") ? (node.at(0).unicode() - 'A') : (node.at(0).unicode() - 'J');
            int count = (node <= "I") ? m_ansColCounts[index].toInt() : m_ansRowCounts[index].toInt();

            // Kiểm tra FULL
            bool isFull = (count == getMaxLed(node));
            if (isFull) {
                m_lockedFull.insert(node); // Khóa vĩnh viễn
                lockAndLightUpFull(node);
            }

            // Bắn tín hiệu sang QML (QML sẽ tự biết đổi màu Đỏ/Xanh dựa vào isFull)
            revealClueToUI("Q4_FULL", node, isFull);

            // Trả về text tương ứng cho OLED
            return isFull ? QString("%1 FULL").arg(node)
                          : QString("%1 NOT FULL").arg(node);
        };

        // Thực thi kiểm tra cho cả 2 nút
        QString result1 = checkNode(m_tempTarget1);
        QString result2 = checkNode(btnId);

        // In 2 dòng kết quả lên OLED đồng thời
        emit oledUpdateRequested(result1, result2);

        m_oledClearTimer->start(3000);
        m_currentState = DEFAULT;
    }
}

void GameBoard::processReview(const QString& btnId) {
    if (btnId < "A" || btnId > "S") return;

    // Phân cấp thứ tự ưu tiên của Review Mode (Không trừ điểm, không dùng Timer)
    if (m_lockedFull.contains(btnId)) {
        // Đã khóa do FULL (ưu tiên cao nhất)
        emit oledUpdateRequested(QString("%1 FULL").arg(btnId), "");
        m_oledClearTimer->start(3000);
    }
    else if (m_askedQ3.contains(btnId)) {
        // Đã từng hỏi Câu 3 -> Biết số lượng chính xác
        int index = (btnId <= "I") ? (btnId.at(0).unicode() - 'A') : (btnId.at(0).unicode() - 'J');
        int count = (btnId <= "I") ? m_ansColCounts[index].toInt() : m_ansRowCounts[index].toInt();

        emit oledUpdateRequested(QString("%1 has %2 demon(s)").arg(btnId).arg(count), "");
        m_oledClearTimer->start(3000);
    }
    else if (m_askedQ4.contains(btnId)) {
        // Đã từng hỏi Câu 4 nhưng không FULL
        emit oledUpdateRequested(QString("%1 not full, guess how many....").arg(btnId), "");
        m_oledClearTimer->start(3000);
    }
    else {
        // Chưa từng hỏi thông tin gì về hàng/cột này
        emit oledUpdateRequested("No cheating...", "");
        m_oledClearTimer->start(3000);
    }
}

int GameBoard::cmpValueForPair(const QString& pair) const {
    // pair đã chuẩn hóa alphabetical, ví dụ "T-U" (không bao giờ "U-T")
    if (pair == "T-U") return m_ansHCmp[0].toInt();
    if (pair == "U-V") return m_ansHCmp[1].toInt();
    if (pair == "W-X") return m_ansHCmp[2].toInt();
    if (pair == "X-Y") return m_ansHCmp[3].toInt();
    if (pair == "T-W") return m_ansVCmp[0].toInt();
    if (pair == "U-X") return m_ansVCmp[1].toInt();
    if (pair == "V-Y") return m_ansVCmp[2].toInt();
    return 0;
}

void GameBoard::processReviewTarget(const QString& btnId) {
    // Không trừ điểm, không dùng timer — giống Review A-S.
    // Dòng 1: đáp án Q1 của LED vừa bấm (nếu đã mua)
    QString line1;
    if (m_askedQ1.contains(btnId)) {
        int index = QString("TUVWXY").indexOf(btnId);
        bool isOdd = m_ansEvenOdd[index].toInt() == 1;
        line1 = QString("%1: %2").arg(btnId, isOdd ? "ODD (.)" : "EVEN (..)");
    } else {
        line1 = QString("%1: No cheating...").arg(btnId);
    }

    // Dòng 2: đáp án Q2 của cặp (nút này + nút T-Y bấm ngay trước đó) nếu cặp đã mua.
    // Muốn xem lại cặp W-X: bấm W rồi bấm X.
    QString line2;
    if (!m_lastReviewTarget.isEmpty() && m_lastReviewTarget != btnId) {
        QString pair = (m_lastReviewTarget < btnId)
                           ? (m_lastReviewTarget + "-" + btnId)
                           : (btnId + "-" + m_lastReviewTarget);
        if (m_askedQ2.contains(pair)) {
            int val = cmpValueForPair(pair);
            QString rel = val > 0 ? ">" : (val < 0 ? "<" : "=");
            line2 = QString("%1 %2 %3").arg(pair.left(1), rel, pair.right(1));
        }
    }
    m_lastReviewTarget = btnId;

    emit oledUpdateRequested(line1, line2);
    m_oledClearTimer->start(3000);
}

// ==========================================================
// CÁC HÀM CŨ TỪ V3 ĐƯỢC GIỮ NGUYÊN (Sinh đề, Cập nhật vạch LED)
// ==========================================================

void GameBoard::tapSegment(int ledIdx, int segIdx) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    if (segIdx < 0 || segIdx >= 7) return;

    if (m_lockedSegments.contains(QString("%1-%2").arg(ledIdx).arg(segIdx))) return;

    QVariantList led = getSegState(ledIdx);
    int cur = led[segIdx].toInt();
    int next = (cur == 0) ? 1 : (cur == 2) ? 1 : 0;
    updateSeg(ledIdx, segIdx, next);
}

void GameBoard::holdSegment(int ledIdx, int segIdx) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    if (segIdx < 0 || segIdx >= 7) return;

    if (m_lockedSegments.contains(QString("%1-%2").arg(ledIdx).arg(segIdx))) return;

    updateSeg(ledIdx, segIdx, 2);
}

void GameBoard::updateSeg(int ledIdx, int segIdx, int val) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    if (segIdx < 0 || segIdx >= 7) return;
    QVariantList led = getSegState(ledIdx);
    led[segIdx] = val;
    m_segStates[ledIdx] = led;
    emit segStatesChanged();
    emit segStateUpdated(ledIdx, led);

    checkWinCondition();
}

void GameBoard::setLedDigit(int ledIdx, int digit) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    QChar ch = QChar::fromLatin1('0' + digit);
    if (DIGIT_MAP.contains(ch)) {
        m_segStates[ledIdx] = DIGIT_MAP[ch];
        emit segStatesChanged();
        emit segStateUpdated(ledIdx, m_segStates[ledIdx].toList());
    }
}

void GameBoard::setLedSegState(int ledIdx, const QVariantList& state) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    m_segStates[ledIdx] = state;
    emit segStatesChanged();
    emit segStateUpdated(ledIdx, state);

    checkWinCondition();
}

QVariantList GameBoard::getSegState(int ledIdx) const {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return QVariantList({0,0,0,0,0,0,0});
    QVariantList result = m_segStates[ledIdx].toList();
    if (result.size() != 7) return QVariantList({0,0,0,0,0,0,0});
    return result;
}

void GameBoard::pauseGame() {
    // Đóng băng toàn bộ đồng hồ
    if (m_globalTimer->isActive()) m_globalTimer->stop();
    if (m_penaltyTimer->isActive()) m_penaltyTimer->stop();
}

void GameBoard::resumeGame() {
    // Chỉ tiếp tục chạy lại khi điểm vẫn còn và game chưa kết thúc
    if (m_points > 0 && !m_secretCode.isEmpty()) {
        m_globalTimer->start(1000);
    }
}

void GameBoard::verifyCode(const QString& guessCode) {
    if (guessCode == m_secretCode) {
        // ĐOÁN ĐÚNG -> KÍCH HOẠT CHIẾN THẮNG
        m_globalTimer->stop();
        if (m_penaltyTimer->isActive()) m_penaltyTimer->stop();
        if (m_oledClearTimer->isActive()) m_oledClearTimer->stop();
        m_secretCode = "";

        int m = m_playTimeSeconds / 60;
        int s = m_playTimeSeconds % 60;
        QString timeStr = QString("%1:%2").arg(m, 2, 10, QChar('0')).arg(s, 2, 10, QChar('0'));
        emit oledUpdateRequested("YOU ESCAPED!", "Clear time: " + timeStr);
        emit gameWon();
    } else {
        // ĐOÁN SAI -> TĂNG BIẾN ĐẾM
        m_guessCount++;

        if (m_guessCount >= 2) {
            // SAI LẦN 2 -> GAME OVER
            m_points = 0;
            emit pointsChanged();

            m_globalTimer->stop();
            if (m_penaltyTimer->isActive()) m_penaltyTimer->stop();
            if (m_oledClearTimer->isActive()) m_oledClearTimer->stop();

            emit oledUpdateRequested("ACCESS DENIED...", "System Locked");
            emit gameLost();
        } else {
            // SAI LẦN 1 -> GỬI TÍN HIỆU CẢNH BÁO (Bật Popup QML)
            emit wrongGuessWarning();
        }
    }
}