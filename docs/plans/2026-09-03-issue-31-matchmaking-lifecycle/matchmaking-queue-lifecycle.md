# Matchmaking Queue Lifecycle

Ticket: [Chốt Match lifecycle cho đường Matchmaking Queue](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/31)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

Decision: HITL grilling with the map owner on 2026-09-03.

## 1. Purpose and scope

This artifact defines the authoritative lifecycle of the **Matchmaking Queue**
for **Ranked Match** only: admission, waiting, cancellation, expiry, Opponent
assignment, Match Start, reconnect, temporal ordering, finalization, and
continuation after a Match.

The HITL decision supersedes only the statement in the
[#25 resolution](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25#issuecomment-5408934507)
that Practice could enter through a queue. Practice Match still starts from a
Room or by choosing a Bot Opponent directly. This artifact does not otherwise
change the Room or Practice lifecycle.

The Queue consumes matching-policy inputs but does not define their values:
Ranked eligibility, pool threshold, counterpart eligibility, pair cooldown,
and `bot_eligible_at` belong to
[Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15).

## 2. Authoritative boundary

- `ENQUEUE_RANKED` is advance consent to the first eligible Opponent assigned
  by the server. A Player cannot inspect, prefer, accept, or reject a candidate.
- A Player may cancel while their Queue Entry is still `WAITING`. Assignment
  and Match Start are one atomic transaction, with no durable `MATCHED` or
  `READY` phase between them.
- After Match Start commits, cancellation is impossible. Forfeit is the only
  voluntary exit from the Match, as required by R-T-06 and R-T-08.
- Authoritative clock time and committed server state are authoritative. Realtime is an
  invalidation hint; it is never a source of truth.
- Player remains a person. A Bot Opponent is never a Player.

## 3. Queue Entry state machine

| State | Meaning | Valid transition |
| --- | --- | --- |
| No effective entry | The Player is outside the Queue | `ENQUEUE_RANKED` to `WAITING` |
| `WAITING` | Consent remains effective and the entry may be assigned | `CONSUMED`, `CANCELLED`, or `EXPIRED` |
| `CONSUMED` | The entry created exactly one Match | None |
| `CANCELLED` | The Player cancelled before assignment | None |
| `EXPIRED` | Hard expiry arrived before assignment | None |

`CONSUMED`, `CANCELLED`, and `EXPIRED` are terminal and absorbing. A terminal
entry never becomes effective again.

### 3.1 Fallback and hard expiry

`bot_eligible_at` makes a `WAITING` entry eligible for Bot fallback; it does
not create a Match by the passage of time alone. The entry's hard expiry is:

```text
expires_at = bot_eligible_at + 60 seconds
```

An authoritative matchmaking observation applies this precedence:

1. At `now >= expires_at`, transition the entry to `EXPIRED`; do not create a
   Match from it.
2. At `bot_eligible_at <= now < expires_at`, assign a Bot Opponent if no
   eligible Player assignment commits.
3. Before `bot_eligible_at`, leave the entry waiting if no eligible Player
   assignment commits.

This gives a disconnected Player a bounded consent window and prevents an old
entry from creating a Match when it is first observed much later. The 60-second
grace is a lifecycle value fixed by this HITL decision; it is not the Bot
fallback duration owned by rating policy.

### 3.2 Authoritative Queue observations

Every `ENQUEUE_RANKED`, `CANCEL_QUEUE`, and `GET_SNAPSHOT` concerning a Queue
Entry is an authoritative Queue observation. Admission by another Player also
runs matching against eligible entries. Each observation MUST apply hard expiry
before cancellation or matching, then attempt matching when the observed entry
remains `WAITING`.

An observation at `bot_eligible_at` is sufficient to activate Bot fallback;
periodic polling is not required by the lifecycle. Reconnect also performs
`GET_SNAPSHOT`. A scheduled sweep MAY create additional observations, but
correctness at the next command, snapshot, or admission MUST NOT depend on it.
Which production mechanism creates observations belongs to the architecture
and UX tickets.

## 4. Admission and matching

`ENQUEUE_RANKED` MUST perform these semantic steps atomically:

1. Read authoritative clock time and materialize due transitions belonging
   to the actor.
2. Lazy-finalize any prior Match that is past its deadline.
3. Re-evaluate current Ranked eligibility.
4. Fail closed if the Player still has an unfinalized Match or an effective
   Queue Entry.
5. Create one `WAITING` Queue Entry.
6. Attempt matching under the current policy inputs.
7. Commit the entry, or commit assignment and Match Start in the same
   transaction.

An idempotent retry returns the effective entry or Match already produced by
the original command; it does not create a second entry.

### 4.1 Player counterpart selection

The matcher MUST:

1. Consider only effective `WAITING` entries allowed by the current matching
   policy.
2. Materialize hard expiry for both entries before evaluating the pair.
3. Skip an ineligible pair without cancelling, consuming, refreshing, or
   reordering either entry.
4. Permit Player-vs-Player assignment only when the pool threshold is met.
5. Select the oldest eligible counterpart, using a stable server-side
   tie-break when enqueue times are equal.
6. Accept no Player-supplied counterpart preference.
7. Re-check entry state, hard expiry, and all pair conditions inside the serialized
   assignment transaction.

For Player-vs-Player, both Queue Entries become `CONSUMED` in the same
transaction that creates exactly one Match. If either entry has already been
cancelled, expired, or consumed, that transaction creates no Match and leaves
the other effective entry waiting.

### 4.2 Bot fallback

If no Player assignment commits and the observed time is within the fallback
window in section 3.1, the transaction assigns a Bot Opponent and consumes the
Player's entry. Exact wait duration and matching thresholds remain policy
inputs; the lifecycle does not copy those numbers into its own contract.

## 5. Cancellation, disconnect, and races

`CANCEL_QUEUE` is valid only for a `WAITING` Queue Entry. Cancellation and
assignment are serialized by committed order:

| First commit | Result |
| --- | --- |
| Cancellation | Entry becomes `CANCELLED`; it cannot be assigned |
| Assignment | Entry becomes `CONSUMED`; cancellation is rejected with the current Match |

Both operations cannot succeed. A retry returns its previously committed
result. Reusing a `command_id` with a different request is rejected.

Disconnect, closing a tab, losing Realtime, refresh failure, or logout does
not cancel a Queue Entry and does not mean Forfeit. Before Match Start, the
entry remains eligible until cancelled, consumed, or expired. After Match
Start, R-S-04 and R-T-07 apply: the Match Clock continues and a Player who does
not return eventually becomes `EXPIRED`.

## 6. Atomic Match Start

The assignment transaction MUST either perform all of the following or perform
none of them:

1. Re-check Queue Entry state, Ranked eligibility, pool threshold, counterpart
   eligibility, and pair restrictions.
2. Select either an Opponent that is another Player or a Bot Opponent.
3. Generate the one shared Ranked Puzzle under R-P-07, R-P-10, and R-P-13.
4. Stamp the exact `ruleset_id`.
5. For a Bot Opponent, stamp the Bot Calibration Profile ID and the
   authoritative pre-Match Ranked Rating snapshot required by that profile.
6. Create the Match and each initial Player State and, where applicable, Bot
   State.
7. Consume the participating Queue Entry or entries.
8. Set `started_at` to the commit timestamp plus 3 seconds.
9. Set `deadline_at = started_at + 900 seconds`.

Gameplay commands are rejected before `started_at`. Once the transaction
commits, R-T-08 forbids cancelling, resetting, or regenerating the Match.

## 7. Temporal ordering and Bot activity

At authoritative clock time `t`, a command, snapshot, or finalization path
MUST first materialize all Match transitions and Bot actions due at or before
`t`, in deterministic timestamp order, and only then evaluate the new request.

Gameplay commands are eligible only in this half-open interval:

```text
started_at <= t < deadline_at
```

At exactly `deadline_at`, expiry is applied before a gameplay command. A Bot
action due at the same timestamp as an observation is applied before that
observation.

For a Match with a Bot Opponent, Match Start binds the exact Ruleset, Bot
Calibration Profile, and Ranked Rating snapshot to a deterministic action
schedule. Due actions have their scheduled Match Clock timestamps even if the
system materializes them later. Bot Score and Solve Time therefore do not
depend on polling, a socket, or a scheduled job firing at the due instant.
Every materialized action remains subject to R-BOT-02 through R-BOT-07; the
lifecycle never assigns Bot Score or a terminal result outside the action
ledger.

The production mechanism that stores or executes the schedule belongs to the
architecture and data-model tickets, not this lifecycle decision.

## 8. Opponent information and reconnect

While waiting, a Player may read only their own Queue Entry state and timing.
The Queue does not expose candidates, pool membership, or information that
would let the Player choose an Opponent. Opponent type and other permitted
details become visible only after irrevocable Match Start. Whether the Ranked
Rating of an Opponent that is another Player is among those details remains
rating-policy input.

During a Player-vs-Player Match, connection information retains the existing
"recently active" semantic inferred from commands and snapshots. It does not
promise true online/offline presence and does not add heartbeat traffic. A Bot
Opponent is always labelled clearly and never receives a fabricated connection
state, as required by R-BOT-10.

Reconnect follows:

```text
connect -> GET_SNAPSHOT -> authoritative snapshot + version
```

The snapshot first applies Queue expiry and matching when the Player remains in
the Queue, or materializes due Match transitions and Bot actions after Match
Start. It then returns the current Queue Entry, committed assignment, or Match.
Information boundaries remain those of R-O-02 and R-BOT-10 until finalization.

## 9. Terminal states and finalization

The terminal and outcome semantics of `digitcode-ruleset/1.0.0` remain
unchanged:

- Player terminal states are absorbing under R-T-02.
- Bot Opponent terminal statuses are `SOLVED`, `ELIMINATED`, or `EXPIRED`; a
  Bot Opponent is never `FORFEITED` (R-BOT-07).
- A Match ends only when Player and Opponent are both terminal (R-T-11 and
  R-BOT-09).
- A Player who becomes terminal first remains read-only while the Opponent
  continues and cannot enter another Match before this Match is finalized.

Command, snapshot, finalization, and admission paths all apply the same lazy,
self-healing transition contract. The transaction that makes the second side
terminal also computes the outcome, records the final result, and commits the
new version atomically. Repeated finalization returns the existing result
without applying another terminal effect. Whether and how Ranked Rating moves
belongs to #15.

A Match past deadline MUST be finalized before either participating Player
starts another Match. A scheduled sweep MAY call the same transition function
as an operational optimization, but correctness MUST NOT depend on that sweep.

## 10. Continuation and command surface

Finalization returns the Player to a state outside the Queue. The consumed
entry never revives, there is no Queue Rematch, and the system does not
auto-requeue. Playing again requires a fresh `ENQUEUE_RANKED`, which supplies
fresh consent and repeats all admission and matching checks.

The Queue adds exactly two state-changing command meanings:

```text
ENQUEUE_RANKED
CANCEL_QUEUE
```

`GET_SNAPSHOT` remains a read path. Each command carries one client-generated
`command_id` preserved across retries. The Room/Practice command contract is
not changed, and the Queue adds no `START_MATCH`, `READY`, `UNREADY`, or
`REMATCH` command.

## 11. Acceptance invariants

The lifecycle is valid only while all of these properties hold:

1. The Matchmaking Queue never creates a Practice Match.
2. One Player has at most one effective Queue Entry and one unfinalized Match,
   and can never have both at once.
3. A Player cannot supply or infer a counterpart preference before Match Start.
4. Both entries apply hard expiry before pair evaluation. Pair rejection
   preserves effective entries; oldest eligible selection and its tie-break are
   deterministic.
5. `WAITING` has exactly three exits, and terminal Queue Entry states never
   revive.
6. At `expires_at`, expiry wins over Bot fallback; before it, an eligible Bot
   fallback may consume the entry.
7. Every Queue command and snapshot applies hard expiry before cancellation or
   matching; cancellation and assignment cannot both commit.
8. Player-vs-Player consumes both entries and creates exactly one Match in one
   transaction.
9. Assignment and Match Start either commit together or roll back together;
   no durable `MATCHED` or `READY` phase exists.
10. `started_at` is commit plus 3 seconds and `deadline_at` is exactly 900
    seconds later. Commands work at `started_at` and fail at `deadline_at`.
11. Due Match transitions and Bot actions are applied before a request at the
    same or a later timestamp.
12. Disconnect cancels neither a Queue Entry nor a Match and never implies
    Forfeit.
13. Reconnect recovers completely from authoritative snapshot plus version.
14. A Match finalizes only after both sides are terminal; the second terminal
    transition and finalization are atomic and idempotent.
15. A Player cannot start another Match before the prior Match is finalized.
16. Disabling all scheduled sweeps does not change eventual correctness at the
    next command, snapshot, finalization, or admission observation.
17. Playing again requires a new Queue Entry; Room and Practice behavior is
    unchanged.

## 12. Ownership exclusions

| Topic | Owner |
| --- | --- |
| Rating eligibility, settlement, cap or saturation, pool threshold, counterpart eligibility, cooldown, and exact Bot fallback time | [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Schema, indexes, Match history, retention, and privacy | [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Queue, countdown, reconnect, activity, and Bot-label presentation | [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Production transport, timer, sweep, and transaction implementation | [Chọn kiến trúc web và managed services](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) |
| Telemetry events, storage, and aggregation | [Chốt telemetry tối thiểu để kiểm chứng cân bằng gameplay](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/35) |

## 13. Canonical references

- [`CONTEXT.md`](../../../CONTEXT.md): Player, Opponent, Bot Opponent, Ranked
  Match, Matchmaking Queue, Queue Entry, Match Start, and Room.
- [ADR 0001](../../adr/0001-ranked-match-leaves-the-room.md): Ranked Match
  leaves Room and comes only from the Matchmaking Queue.
- [Canonical Competitive Game Specification](../2026-08-23-issue-9-game-spec/game-spec.md):
  R-P-07, R-P-10, R-P-13, R-S-02 through R-S-06, R-BOT-01 through R-BOT-11,
  R-T-01 through R-T-08, R-T-11, and R-O-01 through R-O-03.
- [Bot Calibration Profile 1.0.0](../2026-08-31-issue-30-bot-calibration/bot-calibration-profile.md):
  immutable profile binding, Ranked Rating snapshot, deterministic solver, and
  legal Bot action pacing.
- [Chốt mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25#issuecomment-5408934507):
  Queue/Bot model, no Player choice, and the Room decisions superseded for
  Ranked.
- [Chốt Match lifecycle, reconnect và concurrency semantics](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4#issuecomment-5388852395):
  shared Match Start, clock, reconnect, idempotency, and lazy-finalization
  invariants.
- [Nghiên cứu cơ chế scheduled job zero-cost cho Vercel Hobby + Supabase Free](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/27#issuecomment-5390093910):
  a scheduled sweep may optimize but never own correctness.
