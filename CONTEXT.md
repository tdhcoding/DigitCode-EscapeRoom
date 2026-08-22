# DigitCode

DigitCode is a competitive deduction game in which players spend points on clues to discover and draw a six-digit code.

## Language

**Player**:
An authenticated person who participates in a Match.
_Avoid_: User, competitor

**Puzzle**:
A secret six-digit code together with the clue facts derived from it. Both Players in a Match receive the same Puzzle.
_Avoid_: Question, board, level

**Match**:
A real-time head-to-head contest in which exactly two Players independently solve the same Puzzle and are ranked by their performance.
_Avoid_: Game, room, session

**Player State**:
The private, evolving board, clues, score, and guesses belonging to one Player in a Match.
_Avoid_: Match state, shared board

**Score**:
A Player's remaining performance value after clue, elapsed-time, and Wrong Guess costs. Score ranks Players who both Solve the Puzzle.
_Avoid_: Points, Elo, rating

**Solve**:
A Player's successful verification of the Puzzle. A Solve finishes that Player's attempt but does not by itself determine the Match winner.
_Avoid_: Win, victory

**Wrong Guess**:
A valid six-digit code submitted by a Player that does not match the Puzzle. An incomplete or invalid board is not a Wrong Guess.
_Avoid_: Invalid submission, failed verification

**Ranked Match**:
A Match whose final result changes both Players' Elo ratings.
_Avoid_: Competitive game, rated room

**Practice Match**:
A Match that follows the same game rules as a Ranked Match, except that it draws its Puzzle from the unrestricted pool, and that it does not change either Player's Elo rating.
_Avoid_: Casual game, friendly room

**Production MVP**:
The first publicly deployable web release with authentication, online Matches, reconnect-safe results, Match history, and Elo ratings.
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

**Strike**:
A recorded Wrong Guess against one Player in a Match. The second Strike ends that Player's attempt.
_Avoid_: Life, attempt, try

**Forfeit**:
A Player's explicit surrender of a Match. A Forfeit ranks below every other terminal state, so it is a loss whatever the opponent does.
_Avoid_: Quit, abandon, resign

**Draw**:
A Match outcome in which neither Player is ranked above the other.
_Avoid_: Tie, stalemate, no result

**Match Clock**:
The single wall-clock timer of a Match, running from Match start. Score decay, the deadline, and Solve Time all read from it. It never pauses.
_Avoid_: Timer, game clock, play time

**Solve Time**:
The Match Clock reading, in milliseconds, at which a Player's Solve occurred. It breaks ties between Players who Solve with equal Score.
_Avoid_: Clear time, elapsed time, duration

**Ruleset**:
The named, versioned set of game parameters a Match was played under. Every Match record carries one, and only Matches sharing a Ruleset are comparable for Elo.
_Avoid_: Config, settings, rules
