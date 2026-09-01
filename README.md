[![Android Build](https://github.com/mikhailvokhrameev/workout_tracking_app/actions/workflows/Buildozer%20Action.yml/badge.svg)](https://github.com/mikhailvokhrameev/workout_tracking_app/actions/workflows/Buildozer%20Action.yml)

# Mobile App for Tracking Strength Workouts with Progressive Overload Calculation

<div align="center">
<img src="https://github.com/user-attachments/assets/a4f19605-3626-41fb-8151-b996f6f73963" width="150"><br>
</div>

This repository contains an application designed to automate the process of planning and tracking strength training based on the principle of progressive overload. The application can be used by individuals participating in sports at both amateur and professional levels.

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

- **Python 3.12.4**
- **Kivy 2.3.1**
- **kivymd 2.0.1.dev0**
- **kivy-garden 0.1.5**
- **kivy-garden-graph 0.4.1.dev0**

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
│   ├── storage.py --> reading/writing JSON, app data container
│   ├── models.py --> typed models and helpers
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
├──   __init__.py
├──   main.py --> main file, launches the app
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
