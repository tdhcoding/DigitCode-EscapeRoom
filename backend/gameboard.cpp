#include "gameboard.h"
#include <QDebug>

static const QMap<QString, int> SEG_MAP = {
    {"a",0},{"b",1},{"c",2},{"d",3},{"e",4},{"f",5},{"g",6}
};

static const QMap<QString, QStringList> COL_GROUPS = {
    {"0", {"f","e"}},
    {"1", {"a","g","d"}},
    {"2", {"b","c"}}
};

static const QMap<QString, QStringList> ROW_GROUPS = {
    {"0", {"a"}},
    {"1", {"f","b"}},
    {"2", {"g"}},
    {"3", {"e","c"}},
    {"4", {"d"}}
};

static const QMap<QString, QPair<int,int>> COL_LED_MAP = {
    {"A", {0,3}}, {"B", {0,3}}, {"C", {0,3}},
    {"D", {1,4}}, {"E", {1,4}}, {"F", {1,4}},
    {"G", {2,5}}, {"H", {2,5}}, {"I", {2,5}}
};

static const QMap<QString, int> COL_IDX_MAP = {
    {"A",0}, {"B",1}, {"C",2},
    {"D",0}, {"E",1}, {"F",2},
    {"G",0}, {"H",1}, {"I",2}
};

static const QMap<QChar, QVariantList> DIGIT_MAP = {
    {'0', {1,1,1,1,1,1,0}},
    {'1', {0,1,1,0,0,0,0}},
    {'2', {1,1,0,1,1,0,1}},
    {'3', {1,1,1,1,0,0,1}},
    {'4', {0,1,1,0,0,1,1}},
    {'5', {1,0,1,1,0,1,1}},
    {'6', {1,0,1,1,1,1,1}},
    {'7', {1,1,1,0,0,0,0}},
    {'8', {1,1,1,1,1,1,1}},
    {'9', {1,1,1,1,0,1,1}}
};

GameBoard::GameBoard(QObject* parent) : QObject(parent) {
    for (int i = 0; i < 12; i++) {
        m_segStates.append(QVariantList({0,0,0,0,0,0,0}));
    }
}

void GameBoard::setTopDigits(const QString& digits) {
    // 1. Fill LED segments
    for (int i = 0; i < 6; i++) {
        QVariantList segs = {0,0,0,0,0,0,0};
        if (i < digits.size() && DIGIT_MAP.contains(digits[i])) {
            segs = DIGIT_MAP[digits[i]];
        }
        m_segStates[TOP_OFFSET + i] = segs;
        emit segStateUpdated(TOP_OFFSET + i, segs);
    }
    emit segStatesChanged();

    // 2. Chỉ tính khi đủ 6 số
    if (digits.size() < 6) {
        emit topStatsChanged(QVariantMap());
        return;
    }

    QList<QVariantList> st;
    for (int i = 0; i < 6; i++)
        st.append(getSegState(TOP_OFFSET + i));

    QVariantMap stats;

    // 3. Chẵn/lẻ: 0=chẵn, 1=lẻ
    QVariantList evenOdd;
    for (int i = 0; i < 6; i++)
        evenOdd.append(digits[i].digitValue() % 2 == 0 ? 0 : 1);
    stats["evenOdd"] = evenOdd;

    // 4. So sánh ngang: 1=trái lớn, -1=phải lớn, 0=bằng
    // hCmp[0]=T-U, [1]=U-V, [2]=W-X, [3]=X-Y
    auto cmp = [](int a, int b) -> int { return a > b ? 1 : a < b ? -1 : 0; };
    QVariantList hCmp;
    hCmp.append(cmp(digits[0].digitValue(), digits[1].digitValue())); // T vs U
    hCmp.append(cmp(digits[1].digitValue(), digits[2].digitValue())); // U vs V
    hCmp.append(cmp(digits[3].digitValue(), digits[4].digitValue())); // W vs X
    hCmp.append(cmp(digits[4].digitValue(), digits[5].digitValue())); // X vs Y
    stats["hCmp"] = hCmp;

    // 5. So sánh dọc: vCmp[0]=T-W, [1]=U-X, [2]=V-Y
    QVariantList vCmp;
    vCmp.append(cmp(digits[0].digitValue(), digits[3].digitValue())); // T vs W
    vCmp.append(cmp(digits[1].digitValue(), digits[4].digitValue())); // U vs X
    vCmp.append(cmp(digits[2].digitValue(), digits[5].digitValue())); // V vs Y
    stats["vCmp"] = vCmp;

    // 6. Đếm thanh LED sáng theo cột A-I
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

    QVariantList colCounts;
    colCounts.append(countSegs(0, 3, {"f","e"}));     // A
    colCounts.append(countSegs(0, 3, {"a","g","d"})); // B
    colCounts.append(countSegs(0, 3, {"b","c"}));     // C
    colCounts.append(countSegs(1, 4, {"f","e"}));     // D
    colCounts.append(countSegs(1, 4, {"a","g","d"})); // E
    colCounts.append(countSegs(1, 4, {"b","c"}));     // F
    colCounts.append(countSegs(2, 5, {"f","e"}));     // G
    colCounts.append(countSegs(2, 5, {"a","g","d"})); // H
    colCounts.append(countSegs(2, 5, {"b","c"}));     // I
    stats["colCounts"] = colCounts;

    // 7. Đếm thanh LED sáng theo hàng J-S
    auto countRow = [&](QList<int> leds, QStringList segs) -> int {
        int count = 0;
        for (int led : leds)
            for (const QString& s : segs) {
                int idx = SEG_MAP.value(s, -1);
                if (idx >= 0) count += st[led][idx].toInt() > 0 ? 1 : 0;
            }
        return count;
    };

    QVariantList rowCounts;
    rowCounts.append(countRow({0,1,2}, {"a"}));     // J
    rowCounts.append(countRow({0,1,2}, {"f","b"})); // K
    rowCounts.append(countRow({0,1,2}, {"g"}));     // L
    rowCounts.append(countRow({0,1,2}, {"e","c"})); // M
    rowCounts.append(countRow({0,1,2}, {"d"}));     // N
    rowCounts.append(countRow({3,4,5}, {"a"}));     // O
    rowCounts.append(countRow({3,4,5}, {"f","b"})); // P
    rowCounts.append(countRow({3,4,5}, {"g"}));     // Q
    rowCounts.append(countRow({3,4,5}, {"e","c"})); // R
    rowCounts.append(countRow({3,4,5}, {"d"}));     // S
    stats["rowCounts"] = rowCounts;

    emit topStatsChanged(stats);
}

void GameBoard::tapSegment(int ledIdx, int segIdx) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    if (segIdx < 0 || segIdx >= 7) return;
    QVariantList led = getSegState(ledIdx);
    int cur = led[segIdx].toInt();
    int next = (cur == 0) ? 1 : (cur == 2) ? 1 : 0;
    updateSeg(ledIdx, segIdx, next);
}

void GameBoard::holdSegment(int ledIdx, int segIdx) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    if (segIdx < 0 || segIdx >= 7) return;
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
}

void GameBoard::turnOnGroup(int ledIdx, const QStringList& segs, bool emitSignal) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    QVariantList led = getSegState(ledIdx);
    for (const QString& s : segs) {
        int idx = SEG_MAP.value(s, -1);
        if (idx >= 0 && idx < 7) led[idx] = 1;
    }
    m_segStates[ledIdx] = led;
    if (emitSignal) {
        emit segStatesChanged();
        emit segStateUpdated(ledIdx, led);
    }
}

void GameBoard::restoreGroup(int ledIdx, const QStringList& segs,
                             const QVariantList& backup, bool emitSignal) {
    if (ledIdx < 0 || ledIdx >= m_segStates.size()) return;
    QVariantList led = getSegState(ledIdx);
    for (const QString& s : segs) {
        int idx = SEG_MAP.value(s, -1);
        if (idx >= 0 && idx < 7 && idx < backup.size())
            led[idx] = backup[idx];
    }
    m_segStates[ledIdx] = led;
    if (emitSignal) {
        emit segStatesChanged();
        emit segStateUpdated(ledIdx, led);
    }
}

void GameBoard::tapColBtn(const QString& label, int btnState, bool isTop) {
    if (!COL_LED_MAP.contains(label)) return;
    int offset = isTop ? TOP_OFFSET : BOT_OFFSET;
    auto [ledTop, ledBot] = COL_LED_MAP[label];
    ledTop += offset;
    ledBot += offset;
    int colIdx = COL_IDX_MAP[label];
    QStringList segs = COL_GROUPS[QString::number(colIdx)];
    QString key = QString("%1-col-%2").arg(isTop ? "top" : "bot", label);

    if (btnState == 1) {
        QVariantMap b;
        b["led1"] = getSegState(ledTop);
        b["led2"] = getSegState(ledBot);
        m_backups[key] = b;
        turnOnGroup(ledTop, segs, false);
        turnOnGroup(ledBot, segs, false);
        emit segStatesChanged();
        emit segStateUpdated(ledTop, m_segStates[ledTop].toList());
        emit segStateUpdated(ledBot, m_segStates[ledBot].toList());
    } else if (btnState == 2) {
        if (!m_backups.contains(key)) return;
        QVariantMap b = m_backups[key].toMap();
        restoreGroup(ledTop, segs, b["led1"].toList(), false);
        restoreGroup(ledBot, segs, b["led2"].toList(), false);
        emit segStatesChanged();
        emit segStateUpdated(ledTop, m_segStates[ledTop].toList());
        emit segStateUpdated(ledBot, m_segStates[ledBot].toList());
    }
}

void GameBoard::tapRowBtn(const QString& label, int btnState, bool isRow2, bool isTop) {
    const QStringList names1 = {"J","K","L","M","N"};
    const QStringList names2 = {"O","P","Q","R","S"};
    const QStringList& names = isRow2 ? names2 : names1;
    int rowIdx = names.indexOf(label);
    if (rowIdx < 0) return;
    QStringList segs = ROW_GROUPS[QString::number(rowIdx)];
    int offset = (isTop ? TOP_OFFSET : BOT_OFFSET) + (isRow2 ? 3 : 0);
    QString key = QString("%1-row-%2").arg(isTop ? "top" : "bot", label);

    if (btnState == 1) {
        QVariantMap b;
        for (int i = 0; i < 3; i++) {
            b["led"+QString::number(i)] = getSegState(offset + i);
            turnOnGroup(offset + i, segs, false);
        }
        m_backups[key] = b;
        emit segStatesChanged();
        for (int i = 0; i < 3; i++)
            emit segStateUpdated(offset + i, m_segStates[offset + i].toList());
    } else if (btnState == 2) {
        if (!m_backups.contains(key)) return;
        QVariantMap b = m_backups[key].toMap();
        for (int i = 0; i < 3; i++)
            restoreGroup(offset + i, segs, b["led"+QString::number(i)].toList(), false);
        emit segStatesChanged();
        for (int i = 0; i < 3; i++)
            emit segStateUpdated(offset + i, m_segStates[offset + i].toList());
    }
}

void GameBoard::tapCounter(int id, bool isRow) {
    Q_UNUSED(id)
    Q_UNUSED(isRow)
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
}