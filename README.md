[![Android Build](https://github.com/mikhailvokhrameev/workout_tracking_app/actions/workflows/Buildozer%20Action.yml/badge.svg)](https://github.com/mikhailvokhrameev/workout_tracking_app/actions/workflows/Buildozer%20Action.yml)

# Мобильное приложение для отслеживания силовых тренировок с расчетом прогрессивной перегрузки

<div align="center">
<img src="https://github.com/user-attachments/assets/a4f19605-3626-41fb-8151-b996f6f73963" width="150"><br>
</div>


Данный репозиторий содержит приложение, которое предназначено для автоматизации процесса планирования и отслеживания силовых тренировок на основе принципа прогрессивной перегрузки. Использовать приложение могут люди, которые занимаются спортом как на любительском, так и на профессиональном уровне.

---

### Почему я делал этот проект?

Мне хотелось разобраться с процессом разработки полноценного приложения на `Python` и запустить его на мобильном устройстве.
Мне удалось реализовать базу, на основе которой я буду в дальнейшем проводить свои эксперименты в сфере Deep Learning, путем интегрирования ИИ функций в приложение.

---

### Что такое прогрессивная перегрузка?

Это фундаментальный принцип силовых тренировок, который заключается в постепенном увеличении нагрузки на мышцы, чтобы они становились сильнее и больше. **Без постоянного вызова тело человека не будет иметь причин для адаптации.**

**Основная цель** — избежать плато в тренировках. Если выполнять одни и те же упражнения с одинаковым весом и повторениями, тело быстро адаптируется, и прогресс остановится. Прогрессия заставляет мышцы работать усерднее, что стимулирует их гипертрофию и увеличение силы.

В рамках приложения реализовано **3 вида прогрессивной перегрузки**:
* Двойная прогрессия (Double Progression)
* Линейная прогрессия (Linear Progression)

---
### Краткий обзор основных функций

#### Создание тренировочной программы:
<img src="https://github.com/user-attachments/assets/a249a4d3-6c30-4ae0-849b-d751bf028b5e" width="200"><br>

#### Добавление упражнений в программу:
<img src="https://github.com/user-attachments/assets/aa9f57a0-524d-4cf6-86d6-70ae6f887621" width="200"><br>

#### Запись тренировки:
<img src="https://github.com/user-attachments/assets/cea3a130-288e-44d4-bba5-250c69f57ae2" width="200"><br>

#### Просмотр и редактирование истории тренировок:
<img src="https://github.com/user-attachments/assets/c04c65d0-8cc8-42d0-a7b2-19ff44df8157" width="200"><br>

#### Просмотр графиков 1ПМ для любого упражнения:
<img src="https://github.com/user-attachments/assets/70bd01a0-006f-4dff-b007-7d2df06e954d" width="200"><br>

---

### Зависимости:

- **Python 3.12.4**
- **Kivy 2.3.1**
- **kivymd 2.0.1.dev0**
- **kivy-garden 0.1.5**
- **kivy-garden-graph 0.4.1.dev0**

---

### Структура проекта

```
workout_tracking_app/
├── app/
├── kv/
│   ├── components.kv --> некоторые UI компоненты
│   ├── graph_screen.kv
│   ├── history_screen.kv
│   ├── program_detail_screen.kv
│   ├── programs_screen.kv
│   ├── progressive_overload_screen.kv
│   ├── workout_screen.kv
│   └── main_screen.kv --> организации навигации по разным экранам приложения
├── logic/
│   ├── components.py --> некоторые UI компоненты
│   ├── storage.py --> чтение/запись JSON, контейнер данных приложения
│   ├── models.py --> типизированные модели и помощники
│   ├── progression.py
│   ├── services.py --> CRUD для программы/упражнения, сохранение/summary тренировок, история, графики
│   ├── session_state.py
│   └── logic.py --> фасад
├── screens/
│   ├── __init__.py
│   ├── graph_screen.py
│   ├── history_screen.py
│   ├── program_detail_screen.py
│   ├── programs_screen.py
│   ├── progressive_overload_screen.py
│   ├── workout_screen.py
│   ├── main_screen.py --> организации навигации по разным экранам приложения
├──   __init__.py
├──   main.py --> главный файл, запускает приложение
├──   .gitignore
├──   README.md
└──   requirements.txt
```

---

### Установка

Для настройки среды проекта выполните следующее:

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/mikhailvokhrameev/workout_tracking_app.git
    cd workout_tracking_app
    ```

2.  **Создайте и активируйте виртуальное окружение (рекомендуется):**
    ```bash
    # Создание окружения
    python3 -m venv venv

    # Активация на macOS/Linux:
    source venv/bin/activate

    # Активация на Windows:
    venv\Scripts\activate
    ```

3.  **Установите:**
    ```bash
    pip install -r requirements.txt
    ```

---

### Использование

**Важно:** Все команды должны запускаться из корневой папки проекта.

1. Находясь в корневой папке проекта, запустите `main.py`:

```bash
python main.py
```
