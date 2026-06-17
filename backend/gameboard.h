#pragma once
#include <QObject>
#include <QVariantList>
#include <QVariantMap>
#include <QPair>

class GameBoard : public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList segStates READ segStates NOTIFY segStatesChanged)

public:
    explicit GameBoard(QObject* parent = nullptr);
    QVariantList segStates() const { return m_segStates; }

    Q_INVOKABLE void tapSegment(int ledIdx, int segIdx);
    Q_INVOKABLE void holdSegment(int ledIdx, int segIdx);
    Q_INVOKABLE void tapColBtn(const QString& label, int btnState, bool isTop);
    Q_INVOKABLE void tapRowBtn(const QString& label, int btnState, bool isRow2, bool isTop);
    Q_INVOKABLE void tapCounter(int id, bool isRow);
    Q_INVOKABLE void setTopDigits(const QString& digits);
    Q_INVOKABLE void setLedDigit(int ledIdx, int digit);
    Q_INVOKABLE void setLedSegState(int ledIdx, const QVariantList& state);

    Q_INVOKABLE QVariantList getSegState(int ledIdx) const {
        if (ledIdx < 0 || ledIdx >= m_segStates.size())
            return QVariantList({0,0,0,0,0,0,0});
        QVariantList result = m_segStates[ledIdx].toList();
        if (result.size() != 7) return QVariantList({0,0,0,0,0,0,0});
        return result;
    }

signals:
    void segStatesChanged();
    void segStateUpdated(int ledIdx, QVariantList state);
    void topStatsChanged(QVariantMap stats);

private:
    // 12 LED: 0-5 = Top, 6-11 = Bottom
    QVariantList m_segStates;
    QVariantMap  m_backups;

    static const int TOP_OFFSET = 0;
    static const int BOT_OFFSET = 6;

    void updateSeg(int ledIdx, int segIdx, int val);
    void turnOnGroup(int ledIdx, const QStringList& segs, bool emitSignal = true);
    void restoreGroup(int ledIdx, const QStringList& segs,
                      const QVariantList& backup, bool emitSignal = true);
};