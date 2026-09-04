# Player Identity Access-Loss Guarantees

Ticket: [Chốt mức bảo đảm khi Player mất quyền truy cập](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/34)
Map: [Wayfinder: DigitCode web multiplayer production MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/1)

Decision: HITL grilling with the map owner on 2026-09-04.

## 1. Purpose and scope

This artifact defines what the Production MVP guarantees when a Player loses
an anonymous browser session, Google access, email access, or every available
sign-in path. It fixes the boundary between Self-recovery and irreversible
access loss, the continuity promised after successful recovery, and the
prevention and disclosure that the product requires.

This is a planning contract, not a Production MVP implementation. It does not
define storage schema, retention periods, privacy policy, Ranked Rating
settlement, future Ranked eligibility, launch posture, or final UI wording.

## 2. Identity and recovery boundary

- A Player Identity, not a browser session, device, connection, or sign-in
  method, carries continuity of the Player's Ranked Rating, Skill Estimate, and
  Match history.
- Self-recovery succeeds only by authenticating with a Linked Identity that was
  attached to that same Player Identity before access was lost and remains
  accessible to the Player.
- A still-valid authenticated session is current access, not an independent
  Linked Identity. It does not by itself relax the existing recent-authentication
  requirement for linking or unlinking an identity.
- Matching email addresses do not prove that two Player Identities belong to
  the same person. The MVP never auto-merges, manually merges, or transfers
  continuity between them.
- A new anonymous sign-in creates a new Player Identity. It never recovers a
  prior anonymous Player Identity.

## 3. Loss-case guarantees

| Loss case | Self-recovery guarantee | Continuity and limits |
| --- | --- | --- |
| Anonymous browser session lost before any identity is linked | None. Access to the old Player Identity is irreversible within the product guarantee. | A new anonymous sign-in creates a new Player Identity. The old Skill Estimate and Match history are not transferred. No Ranked Rating exists to recover because Ranked requires Google under the current policy. |
| Google access lost; linked email remains accessible | Signing in through that linked email returns the same Player Identity. | Ranked Rating, Skill Estimate, and retained Match history remain associated with that identity. Magic-link delivery remains subject to quota and deliverability and is not promised to be immediate. Whether the Player remains eligible for future Ranked Matches is owned by rating policy. |
| Email access lost; linked Google remains accessible | Signing in through that linked Google identity returns the same Player Identity. | Ranked Rating, Skill Estimate, and retained Match history remain associated with that identity. |
| Google and email access both lost, with no valid authenticated session | None. Access to the old Player Identity is irreversible within the product guarantee. | The Player may create a new Player Identity, but it does not inherit or merge the old Ranked Rating, Skill Estimate, or Match history. |
| Access to one or more Linked Identities lost while an authenticated session remains valid | The session may continue to provide access until it expires or is revoked, but it is not Self-recovery. | Linking or unlinking still requires recent authentication. If that control cannot be satisfied through an accessible identity, the session alone cannot establish a new Linked Identity. |

Successful Self-recovery MUST return the same canonical Player Identity and
therefore the same Ranked Rating and Skill Estimate. It MUST expose Match
history still available under the retention and authorization policy later
defined by
[Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14).

Access loss by itself neither deletes retained data nor reverses a Match result,
Ranked Rating change, or settlement. This contract makes no promise that data
which a Player can no longer access will be retained forever.

## 4. Linked Identity management

- A Player may attach multiple Linked Identities only from an authenticated
  session and subject to the canonical recent-authentication control.
- If the Google or email identity being attached already belongs to another
  Player Identity, linking MUST fail. Neither Player Identity changes, no
  rating or history moves, and no operator reconciliation path is offered.
- Once a Player Identity has at least one Linked Identity, the product MUST
  reject unlinking its final Linked Identity. Player Identity deletion remains
  a separate action outside this access-loss contract.
- Unlinking one of two remaining Linked Identities is allowed after recent
  authentication and an explicit warning that only one Linked Identity will
  remain.

These controls reduce preventable orphaning. They do not guarantee continued
access to a provider account that is suspended, deleted, compromised, or
otherwise made unavailable outside DigitCode.

## 5. Mandatory disclosure

The Production MVP MUST:

1. Before an anonymous Player's first Practice Match, state that signing out,
   clearing browser data, or moving to another device before linking an identity
   can permanently remove access to that Player Identity, its Skill Estimate,
   and its Match history. This disclosure MUST NOT block anonymous play.
2. Keep a discoverable identity settings view showing the Linked Identities
   currently attached and warn when only one Linked Identity remains. For an
   anonymous Player with none, this view MUST repeat the irreversible-loss
   disclosure from item 1.
3. Explain the concrete access-loss consequence before unlinking an identity
   and reject unlinking the final Linked Identity.
4. When Self-recovery is unavailable, state that the MVP has no operator or
   manual identity-recovery path. It MUST NOT imply that contacting support can
   restore access.
5. Present linking Google or email as prevention, not as a promise of recovery
   after the anonymous session has already been lost.

The MVP does not repeat the anonymous warning before every Match and does not
promise to detect browser-data deletion or loss of a provider account outside
the application. Exact placement, interaction design, and Vietnamese copy
belong to
[Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13).
The public beta label and launch-level presentation of these limits belong to
[Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17).

## 6. Queue Entry and Match continuity

Identity access loss adds no Queue Entry or Match transition. Disconnect,
closing a tab, losing Realtime, refresh failure, or logout continues to follow
the canonical Matchmaking Queue lifecycle:

- it cancels neither a Queue Entry nor a Match;
- it never implies Forfeit;
- a waiting Queue Entry remains effective until consumed, cancelled, or expired;
- after Match Start, the Match Clock continues and an absent Player may become
  `EXPIRED`;
- final result and Ranked Rating settlement follow their canonical policies and
  are not reversed because a Player lost access.

Reconnect through a still-authorized Player Identity recovers authoritative
state from snapshot plus version. That connection guarantee does not recover a
Player Identity for someone who can no longer authenticate as it.

## 7. Explicit non-guarantees

The Production MVP does not promise:

- operator recovery or transfer of a Player Identity;
- manual identity proof or support-mediated Linked Identity replacement;
- auto-merge based on matching email addresses;
- recovery by creating a new anonymous or provider account;
- database restore as an individual Player Identity recovery mechanism;
- immediate delivery of every email magic link;
- retention of Match history outside the policy later chosen by its owner.

## 8. Acceptance contract

An implementation conforms only if automated tests and review establish all of
the following:

1. Reauthentication with either accessible Linked Identity resolves to the
   same stable Player Identity and does not create a second rating or history.
2. Losing an unlinked anonymous session and signing in anonymously again yields
   a different Player Identity with no inherited Skill Estimate or history.
3. A same-email identity that was not previously linked cannot claim or merge
   another Player Identity.
4. Linking an identity already owned by another Player Identity fails without
   changing either side.
5. Unlinking the final Linked Identity fails; unlinking one of exactly two
   succeeds only after recent authentication and disclosure that one will remain.
6. A surviving session cannot bypass recent authentication to establish or
   remove a Linked Identity.
7. Access loss triggers no cancellation, Forfeit, result reversal, or Ranked
   Rating reversal.
8. Anonymous first-Match, identity settings, single-identity, unlink, and
   unrecoverable-loss surfaces carry every mandatory disclosure from section 5,
   including that linking is prevention rather than post-loss recovery.

## 9. Ownership exclusions

| Topic | Owner |
| --- | --- |
| Schema, retention, storage deletion, Match history authorization, and privacy | [Chốt data model, lịch sử đấu và quyền riêng tư](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/14) |
| Future Ranked eligibility after Google access is lost, settlement, correction, and rating integrity | [Chốt chính sách Elo và result integrity](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/15) |
| Exact recovery, identity settings, warning, and error presentation | [Prototype trải nghiệm web end-to-end](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/13) |
| Public launch wording, support expectations, and zero-cost beta posture | [Chốt launch posture cho zero-cost MVP](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/17) |
| Auth provider, session, database, and deployment implementation | [Chọn kiến trúc web và managed services](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/3) |

## 10. Canonical references

- [`CONTEXT.md`](../../../CONTEXT.md): Player, Player Identity, Linked Identity,
  Self-recovery, Ranked Rating, Skill Estimate, and Production MVP.
- [Chốt identity, profile và invite-room lifecycle](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2#issuecomment-5388396390):
  Google and email identities, linking only from an authenticated session,
  no auto-merge, and Player Identity deletion semantics.
- [Chốt mô hình đối thủ của Ranked Match](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25#issuecomment-5408934507):
  anonymous Player Identity, Google linking, and Skill Estimate continuity.
- [Nghiên cứu cách Supabase tính MAU cho phiên ẩn danh](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/33#issuecomment-5411784888):
  anonymous sign-in creates an Auth user and linking Google into the current
  user is supported.
- [Chốt threat model và anti-cheat boundary](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/12#issuecomment-5427620927):
  recent authentication for identity changes and authenticated actor authority.
- [Matchmaking Queue Lifecycle](../2026-09-03-issue-31-matchmaking-lifecycle/matchmaking-queue-lifecycle.md):
  disconnect, expiry, reconnect, and finalization semantics.
- [Zero-cost Vercel Architecture Research](../../research/2026-08-22-zero-cost-vercel-architecture.md):
  no unconditional production-grade guarantee, no automatic Supabase Free
  backup or uptime SLA, and email quota and deliverability limits.
