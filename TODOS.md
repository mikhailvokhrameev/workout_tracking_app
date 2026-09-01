# TODOS

## P1 — Commit buildozer.spec, verify sqlite3 build requirement
**What:** Commit `buildozer.spec` (or a secrets-safe template) and confirm `sqlite3` is listed in its `requirements =` line.
**Why:** `buildozer.spec` is gitignored (`*.spec`) and not tracked, so the CI Buildozer Action can't reproduce a build from a fresh clone, and it's unverified whether the Android build actually includes the `sqlite3` module. python-for-android has a history of `_sqlite3` build-order bugs (see kivy/python-for-android#1053, #1564). Severity note from the eng review's outside voice: since local dev runs on desktop Python (where stdlib sqlite3 always exists), this bug has **no repro path in dev** — it would only surface as a silent total failure on an actual Android build/device, with no CI signal today. Verify before shipping the DB refactor to Android, not after.
**Context:** Discovered during the JSON→SQLite storage refactor review (2026-09-01). `.github/workflows/Buildozer Action.yml` already installs `libsqlite3-dev`/`sqlite3` as system build deps, which is a good sign, but the actual `android.requirements` line in `buildozer.spec` couldn't be checked since the file isn't in git.
**Priority:** P1 — blocks confidently shipping the SQLite refactor to Android.
**Effort:** S (human ~30min / CC ~5min).

## P2 — Full test coverage for app/logic/progression.py
**What:** Unit tests for `calculate_next_target`, `check_goal_achievement`, `calculate_one_rep_max` across linear and double progression types.
**Why:** 168 lines of core domain logic (the thing users rely on the app to get right) with zero test coverage today. The SQLite refactor only adds regression tests for the specific call sites it rewrites, not full coverage of this file's logic.
**Context:** Discovered during the JSON→SQLite storage refactor review (2026-09-01); this file already had a stale commented-out code block removed this session, suggesting it's evolved without a safety net.
**Priority:** P2.
**Effort:** M (human ~half day / CC ~20-30min).
**Depends on / blocked by:** none — independent of the storage refactor.
