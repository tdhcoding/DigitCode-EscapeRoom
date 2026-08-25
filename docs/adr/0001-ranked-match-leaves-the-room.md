# Ranked Match leaves the Room and comes only from the Matchmaking Queue

The invite-room model built by [#2](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/2)
and [#4](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/4) lets a Player **choose
their Opponent**, which is sufficient for one person running two accounts to move rating
between them. Because the accepted risk for that was fixed at **zero**, a Ranked Match no
longer comes from a Room: it comes from the **Matchmaking Queue**, and when no Player is
available it is played against a **Bot Opponent** whose strength tracks that Player's own
Ranked Rating — so a rating converges on true strength and stops there, making a climb past
true strength mathematically impossible rather than merely expensive.

The full decision, with every number, is the **resolution comment on
[#25](https://github.com/tdhcoding/DigitCode-EscapeRoom/issues/25)**. This document
deliberately does **not** restate it: two records of one decision are two records that will
drift apart.

## Why the cheaper option was rejected

A pure-policy lever was costed before the destination was redrawn: **an early Forfeit
transfers zero rating**. It is genuinely cheap — Elo is not part of the Ruleset (R-K-02 lists
8 configurable parameters, none of them an Elo parameter), so no version bump and no R-K-04
history cut; and `T = 0` is symmetric, so the zero-sum proof in #10 §1.3 survives intact. It
also lands on the right spot: under R-T-04 and R-T-05.4, **every winning path other than
R-T-05.3 requires a real Solve**, so removing the rating value of an early Forfeit removes
every sub-minute win.

But it buys only about **20×** (the 23-donor path moves from 28 minutes to 9.2 hours), because
an attacker simply waits out the threshold or switches to "donor self-eliminates, booster
really Solves". Every lever available at the rating-policy layer attacks the **price per
rating point**; none attacks the **choice of opponent**. A requirement of zero is reachable
only by removing that choice.

## Non-obvious consequences

- **Room, Invite Code, Seat and Room Owner still exist, but serve Practice only.** Do not
  "fix" this: that machinery looking redundant for Ranked is **deliberate**, not an oversight.
- **The rating system is now hybrid**: Player against Player stays zero-sum `+T/−T`; Player
  against Bot Opponent moves one rating only. #10 §1.3/§4.1/§4.2/§5.3 must be re-read with
  that in mind.
- **#10 §4.1 no longer constrains this design.** The disconnected-component problem is solved
  **structurally**: every Player is measured by the same `Ranked Rating → target Score`
  function. What makes ratings comparable is a shared **yardstick**, not a shared **node** — a
  Bot Opponent is not a hub, because it carries no information between two Players.
- **The integrity of the whole ladder now rests on that calibration function**, and the
  function does not exist yet. Wherever it is not monotone, that band of the ladder is wrong
  **silently**, with no symptom.
- **Parts of #2 and #4 are void** — the exact list lives in the resolution comment on #25.
