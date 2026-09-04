# DigitCode

DigitCode is a competitive deduction game in which players spend points on clues to discover and draw a six-digit code.

## Language

**Player**:
A person who participates in a Match, whether or not they have signed up. A Bot Opponent is never a Player.
_Avoid_: User, competitor, guest

**Player Identity**:
A durable identity under which the system associates a Player with their Ranked Rating, Skill Estimate, and Match history. It is independent of any browser session, device, connection, or sign-in method.
_Avoid_: Account, user, session, provider identity

**Linked Identity**:
A Google or email identity that a Player has attached to a Player Identity and can use to authenticate access to it.
_Avoid_: Provider, login, recovery code

**Self-recovery**:
Regaining access to the same Player Identity by authenticating with an accessible Linked Identity, without operator intervention, manual identity proof, Player Identity merging, or database restoration.
_Avoid_: Account recovery, restore, merge

**Puzzle**:
A secret six-digit code together with the clue facts derived from it. Both sides of a Match receive the same Puzzle.
_Avoid_: Question, board, level

**Match**:
A real-time head-to-head contest in which a Player and one Opponent independently solve the same Puzzle and are ranked by their performance.
_Avoid_: Game, room, session

**Opponent**:
The other side of a Match, seen from one Player. An Opponent is either another Player or a Bot Opponent.
_Avoid_: Rival, enemy, the other player

**Bot Opponent**:
A program that takes one side of a Match in place of a Player. It holds no identity and carries no Ranked Rating, and is never presented as a Player.
_Avoid_: AI, computer, second player, bot player

**Bot Calibration Profile**:
An immutable, versioned contract that maps a pre-Match Ranked Rating snapshot to Bot Opponent inference and pacing behavior under exactly one Ruleset.
_Avoid_: Bot difficulty, calibration config, rating formula

**Player State**:
The private, evolving board, clues, score, and guesses belonging to one Player in a Match.
_Avoid_: Match state, shared board

**Bot State**:
The private, evolving clues, Bot Score, candidate submissions, and Bot Terminal Status belonging to one Bot Opponent in a Match. It never contains a Player Board.
_Avoid_: Player State, bot board, shared state

**Score**:
A Player's remaining performance value after clue, elapsed-time, and Wrong Guess costs. When both sides Solve the Puzzle, it is compared with the Opponent's Score or Bot Score.
_Avoid_: Points, Elo, rating

**Bot Score**:
A Bot Opponent's remaining performance value after clue, elapsed-time, and incorrect Bot Submission costs. It is distinct from every Player's Score.
_Avoid_: Score, bot points, target score

**Ranked Rating**:
The public number that ranks a Player against every other Player on one scale. It is the only rating a Player can see.
_Avoid_: Elo, MMR, rank

**Skill Estimate**:
The system's private estimate of a Player's true strength, informed by every Match they play. It is never shown to a Player.
_Avoid_: Hidden Elo, MMR, true rating

**Solve**:
A successful answer to the Puzzle: a Player produces it through Verify, and a Bot Opponent through Bot Submission. A Solve finishes that side's attempt but does not by itself determine the Match winner.
_Avoid_: Win, victory

**Wrong Guess**:
A valid six-digit code submitted by a Player that does not match the Puzzle. An incomplete or invalid board is not a Wrong Guess.
_Avoid_: Invalid submission, failed verification

**Ranked Match**:
A Match whose final result changes the Ranked Rating of every Player in it. Every Ranked Match begins in the Matchmaking Queue.
_Avoid_: Competitive game, rated room

**Practice Match**:
A Match that follows the same game rules as a Ranked Match, except that it draws its Puzzle from the unrestricted pool, and that it moves no one's Ranked Rating. It still informs the Skill Estimate of each Player in it.
_Avoid_: Casual game, friendly room

**Production MVP**:
The first publicly deployable web release with sign-in, online Matches, reconnect-safe results, Match history, and Ranked Ratings.
_Avoid_: Prototype, demo

**Player Board**:
The 2x3 grid of seven-segment LEDs that one Player draws on during a Match. Each of its 42 LED-segment cells is either off or on. Only that Player writes to it; a Clue never does.
_Avoid_: Board, grid, canvas

**Clue**:
A purchasable fact about the Puzzle. A Clue names one target and returns information only — it never changes the Player Board.
_Avoid_: Question, hint, Q1/Q2/Q3

**Verify**:
The explicit action by which a Player submits their decoded Player Board as an answer. Verify is the only action that can produce a Solve.
_Avoid_: Check, submit, guess

**Bot Submission**:
The explicit action by which a Bot Opponent submits one six-digit candidate as its answer.
_Avoid_: Verify, bot guess, automatic Solve

**Strike**:
A recorded Wrong Guess against one Player in a Match. The second Strike ends that Player's attempt.
_Avoid_: Life, attempt, try

**Forfeit**:
A Player's explicit surrender of a Match. A Forfeit ranks below every other terminal state, so it is a loss whatever the Opponent does.
_Avoid_: Quit, abandon, resign

**Bot Terminal Status**:
The terminal label of a Bot Opponent: SOLVED, ELIMINATED, or EXPIRED. A Bot Opponent never has FORFEITED status.
_Avoid_: Player State, bot result, FORFEITED bot

**Draw**:
A Match outcome in which neither side is ranked above the other.
_Avoid_: Tie, stalemate, no result

**Match Clock**:
The single wall-clock timer of a Match, running from Match Start. Score decay, the deadline, and Solve Time all read from it. It never pauses.
_Avoid_: Timer, game clock, play time

**Solve Time**:
The Match Clock reading, in milliseconds, at which a Player's or Bot Opponent's Solve occurred. It breaks a tie after their two Scores, or the Player's Score and the Bot Opponent's Bot Score, are equal.
_Avoid_: Clear time, elapsed time, duration

**Ruleset**:
The named, versioned set of game parameters a Match was played under. Every Match record carries one, and only Matches sharing a Ruleset are comparable for Ranked Rating.
_Avoid_: Config, settings, rules

**Matchmaking Queue**:
The one place a Player waits to be given an Opponent for a Ranked Match. No Player chooses who they are matched with.
_Avoid_: Lobby, matchmaking, pool, ladder

**Queue Entry**:
A Player's revocable consent to receive the first eligible Opponent assigned by the Matchmaking Queue for one Ranked Match. It ends when consumed, cancelled, or expired.
_Avoid_: Lobby slot, challenge, opponent request, ready state

**Room**:
The durable meeting place a Room Owner opens to invite one other Player into Practice Matches. A Room outlives the Matches played in it, and no Ranked Match is ever played in one.
_Avoid_: Lobby, session, game, match

**Room Owner**:
The Player who created a Room. Ownership confers the right to close the Room while it holds no unfinished Match, and nothing more.
_Avoid_: Host, admin, creator

**Invite Code**:
The single short secret that admits one other Player to a Room, shared either as a bare code or embedded in a link. It is consumed permanently at Match Start and is never reissued.
_Avoid_: Room code, token, link, password

**Seat**:
One of a Room's two places, held by a Player rather than by a device or connection. One Player never holds both Seats, and one Seat may be watched from several devices at once.
_Avoid_: Slot, connection, session, client

**Match Start**:
The single moment at which a Match comes into existence: its Puzzle is generated, its Ruleset is stamped, any Invite Code that led to it dies, and its Match Clock is scheduled. Nothing may cancel a Match afterwards.
_Avoid_: Kickoff, game start, countdown, ready

**Rematch**:
A further Match played in the same Room, on a new Puzzle, agreed to by both Players. It is always a new Match record, never a replay of an old one.
_Avoid_: Replay, restart, next round

**Player Tag**:
The short immutable label carried alongside a Player's display name, which distinguishes Players who chose the same name. Display names are never shown without it.
_Avoid_: Username, handle, discriminator, ID
