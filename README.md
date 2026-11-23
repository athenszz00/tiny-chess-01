# tiny-chess-01 — 0x88 Chess Engine

A from-scratch chess engine in a single Python file, built for the
make.fun tiny-chess-01 competition. No chess libraries: board, move
generation, search, and evaluation are all hand-written.

## The engine

- **0x88 board representation** — 128-square board with off-board detection
  built into the square index.
- **Negamax search with alpha-beta pruning**, plus quiescence search to
  settle captures before evaluation.
- **Transposition table with Zobrist hashing**, move ordering, and
  piece-square-table evaluation.
- **Fixed 100,000-node search budget** per move, so strength is comparable
  across hardware.

## Results

- Practice Elo ~1,396 average in local trials.
- make.fun server practice grade **1,545** — reached the final.
- Dev-phase rank 518 of 4,344 entries.

## How it plays

The engine is an HTTP client for the make.fun tiny-chess harness: it polls
the harness server for the game state and posts its moves back.

```
MAKEFUN_ENV_URL=http://localhost:PORT python3 engine.py
```

`MAKEFUN_ENV_URL` must point at the harness server (provided by the
make.fun competition kit). The engine loops games until the harness reports
done, then prints the final wins, draws, and losses.

## Files

- `engine.py` — the readable engine source.
- `build.py` — regenerates the compressed submission build (`main.py`) from
  `engine.py`. The submitted build is the engine compressed with LZMA
  (alone format, 16 KiB dictionary); `build.py` produces an equivalent
  build that decompresses to the same source. Run it with
  `python3 build.py`.

## Built by

Built by Muse, Meta's personal AI agent, for the make.fun tiny-chess-01
competition.
