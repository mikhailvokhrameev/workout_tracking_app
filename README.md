[![Android Build](https://github.com/mikhailvokhrameev/workout_tracking_app/actions/workflows/Buildozer%20Action.yml/badge.svg)](https://github.com/mikhailvokhrameev/workout_tracking_app/actions/workflows/Buildozer%20Action.yml)

# Mobile App for Tracking Strength Workouts with Progressive Overload Calculation

<div align="center">
<img src="https://github.com/user-attachments/assets/a4f19605-3626-41fb-8151-b996f6f73963" width="150"><br>
</div>

This repository contains an application designed to automate the process of planning and tracking strength training based on the principle of progressive overload. The application can be used by individuals participating in sports at both amateur and professional levels.

---

## Stack

`Python` · `Kivy` · `KivyMD` · `SQLite` · `kivy_garden.graph` · `Buildozer` · `pytest`

---

### Why did I build this project?

I wanted to understand the process of developing a full-featured application in `Python` and launching it on a mobile device.
I managed to implement a foundation upon which I will conduct my future experiments in Deep Learning by integrating AI features into the app.

---

### What is progressive overload?

It is a fundamental principle of strength training that involves gradually increasing the stress placed upon the muscles so that they become stronger and larger. **Without a constant challenge, the human body will have no reason to adapt.**

**The main goal** is to avoid training plateaus. If you perform the same exercises with the same weight and reps, the body quickly adapts, and progress stops. Progression forces the muscles to work harder, stimulating hypertrophy and strength gains.

The app implements **3 types of progressive overload**:
* Double Progression
* Linear Progression

| Feature | Demonstration |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Creating a workout program** | <a href="https://github.com/user-attachments/assets/a249a4d3-6c30-4ae0-849b-d751bf028b5e"><img src="https://github.com/user-attachments/assets/a249a4d3-6c30-4ae0-849b-d751bf028b5e" width="200"></a> |
| **Adding exercises to a program** | <a href="https://github.com/user-attachments/assets/aa9f57a0-524d-4cf6-86d6-70ae6f887621"><img src="https://github.com/user-attachments/assets/aa9f57a0-524d-4cf6-86d6-70ae6f887621" width="200"></a> |
| **Logging a workout** | <a href="https://github.com/user-attachments/assets/cea3a130-288e-44d4-bba5-250c69f57ae2"><img src="https://github.com/user-attachments/assets/cea3a130-288e-44d4-bba5-250c69f57ae2" width="200"></a> |
| **Viewing and editing workout history** | <a href="https://github.com/user-attachments/assets/c04c60d0-8cc8-42d0-a7b2-19ff44df8157"><img src="https://github.com/user-attachments/assets/c04c60d0-8cc8-42d0-a7b2-19ff44df8157" width="200"></a> |
| **Viewing 1RM charts for an exercise** | <a href="https://github.com/user-attachments/assets/70bd01a0-006f-4dff-b007-7d2df06e954d"><img src="https://github.com/user-attachments/assets/70bd01a0-006f-4dff-b007-7d2df06e954d" width="200"></a> |


### Dependencies:

- **Python 3.12.4** — the interpreter, installed separately (not via `pip`)
- **Kivy 2.3.1**
- **KivyMD 2.0.1.dev0** — pinned to commit [`95184d9`](https://github.com/kivymd/KivyMD/tree/95184d98c6215a3f5cc0821708628963b654a59e)
- **kivy-garden 0.1.5**
- **kivy_garden.graph 0.4.1.dev0** — pinned to commit [`27c93e0`](https://github.com/kivy-garden/graph/tree/27c93e044cdae041c3fd1c98548bce7494f61e9e)
- **materialyoucolor 2.0.10** — pulled in by KivyMD, pinned deliberately (see below)
- **sqlite3** (Python standard library) — ground-truth storage, see [Data layer](#data-layer) below

KivyMD and `kivy_garden.graph` are installed **from git at exact commits**, because neither is on PyPI at the version this app needs — both report `.dev0` versions that exist only on their master branches.

Those pins are load-bearing rather than housekeeping. `2.0.1.dev0` is the version string KivyMD master has carried for over a year, so it identifies nothing: KivyMD master later started importing `materialyoucolor.dynamiccolor.color_spec`, which materialyoucolor 2.0.10 does not provide. Tracking master produced an Android build that compiled cleanly and then died at startup with `ModuleNotFoundError`. `buildozer.spec` pins KivyMD to the same commit — **keep the two in sync**.

---

### Data layer

App data (programs, exercises, workout history, progression targets) lives in a normalized **SQLite** database, not a JSON blob — `programs`, `exercises`, `workout_sessions`, `session_exercises`, and `sets` tables, plus an `app_meta` key/value table for settings and schema versioning. A repository layer (`ProgramRepository`, `WorkoutRepository`, `SettingsRepository`) owns all reads and writes, sharing a single connection; the service layer never touches SQL directly.

On first launch after an upgrade from an older version, a one-time transactional migration imports the legacy `app_data.json` into the database and renames it to `app_data.json.bak` — safe to interrupt: if the app is killed mid-migration, the next launch retries cleanly instead of leaving partial data.

This move away from a single JSON file was specifically to make the data queryable — the normalized schema is what future ML-driven features (progression trend analysis, plateau detection) will read from directly with SQL, instead of deserializing and looping over the whole history in Python.

---

### Project Structure

```
workout_tracking_app/
├── app/
├── kv/
│   ├── components.kv --> some UI components
│   ├── graph_screen.kv
│   ├── history_screen.kv
│   ├── program_detail_screen.kv
│   ├── programs_screen.kv
│   ├── progressive_overload_screen.kv
│   ├── workout_screen.kv
│   └── main_screen.kv --> organizing navigation across different app screens
├── logic/
│   ├── components.py --> some UI components
│   ├── schema.py --> SQLite schema (tables, indexes, schema_version)
│   ├── database.py --> connection bootstrap: creates schema, runs migration
│   ├── migration.py --> one-time transactional import from legacy app_data.json
│   ├── repositories.py --> ProgramRepository, WorkoutRepository, SettingsRepository — all SQL lives here
│   ├── dataclasses.py --> typed Program/Exercise/WorkoutSession/... records returned by the repositories
│   ├── errors.py --> StorageWriteError + rollback-on-failure wrapper for writes
│   ├── progression.py
│   ├── services.py --> CRUD for program/exercise, saving/summary of workouts, history, charts
│   ├── session_state.py
│   └── logic.py --> facade
├── screens/
│   ├── __init__.py
│   ├── graph_screen.py
│   ├── history_screen.py
│   ├── program_detail_screen.py
│   ├── programs_screen.py
│   ├── progressive_overload_screen.py
│   ├── workout_screen.py
│   └── main_screen.py --> organizing navigation across different app screens
├── tests/ --> pytest suite: repository CRUD, migration, progression logic, error handling
├── ci/
│   └── smoke_test.sh --> boots the app on a CI emulator and dumps the Python log
├── .github/workflows/
│   └── Buildozer Action.yml --> Android build matrix + emulator smoke test
├──   __init__.py
├──   main.py --> main file, launches the app
├──   buildozer.spec --> Android packaging config
├──   .gitignore
├──   README.md
└──   requirements.txt
```

---

### Installation

To set up the project environment, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mikhailvokhrameev/workout_tracking_app.git
   cd workout_tracking_app
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   # Create environment
   python3 -m venv venv

   # Activation on macOS/Linux:
   source venv/bin/activate

   # Activation on Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Usage

**Important:** All commands must be run from the root directory of the project.

1. Being in the root directory of the project, run `main.py`:

```bash
python main.py
```

2. Run the test suite:

```bash
python -m pytest tests/
```

---

### Android build

The APK is built with **Buildozer** / python-for-android, configured in `buildozer.spec`.

```bash
# Debug APK for a real device (arm64-v8a) -> bin/wtrackerApk-0.1-arm64-v8a-debug.apk
buildozer -v android debug

# x86_64 build, used only for testing on an emulator
buildozer -v --profile ci android debug
```

**Architectures.** Only `arm64-v8a` is shipped. Every additional arch duplicates the entire native payload — `libpybundle.so` alone is ~16 MB per arch — so building `arm64-v8a` and `x86_64` together produced a 53 MB APK of which roughly half was libraries no phone could execute. Restricting to `arm64-v8a` puts the debug APK at ~26 MB.

x86_64 is still needed to install on a GitHub-hosted emulator, so it lives in a separate `[app@ci]` profile at the bottom of `buildozer.spec` rather than in the shipped configuration.

**`minapi` is 24, not 23.** CPython's `remote_debugging.c` uses `preadv`/`pwritev`, which the NDK only declares from API 24; on 23 the build fails to compile.

### Continuous integration

`.github/workflows/Buildozer Action.yml` runs on pushes and PRs to `main`, and on demand via `workflow_dispatch` for any branch. It builds two legs in parallel:

| Leg | Arch | Purpose |
|---|---|---|
| `build (arm64-v8a)` | arm64-v8a | Produces the uploaded APK artifact |
| `build (x86_64)` | x86_64 | Boots an emulator and runs the runtime smoke test |

**Why a smoke test.** A green build says nothing about whether the app actually runs. The app once built successfully and then died on the presplash on every launch — and because python-for-android exits the process cleanly when Python raises during startup, that is not a Java crash or an ANR, so Firebase Test Lab reported *"no crashes"* while the app had never started. `ci/smoke_test.sh` installs the APK, launches it through the LAUNCHER intent, and dumps `logcat -s python`, making startup tracebacks visible in CI without a physical device. A healthy run reaches:

```
[INFO] [Base] Start application main loop
PROCESS IS RUNNING (app survived startup)
```

The smoke test never fails the build on a crashing app — the captured log is the deliverable.

**Caching.** The `.buildozer` cache key includes a hash of `buildozer.spec` and the matrix leg name. Both matter: a static key once restored p4a's per-target build tree even after `android.minapi` changed, silently rebuilding against the old target, and an unscoped key would let one arch's leg save a cache the other then restores without its own build tree.
