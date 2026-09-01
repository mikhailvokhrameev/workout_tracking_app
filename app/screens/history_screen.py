# -*- coding: utf-8 -*-

from __future__ import annotations
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock


def _logic():
    return MDApp.get_running_app().logic


class HistoryExerciseItem(MDBoxLayout):
    exercise_name = StringProperty("")
    sets_summary = StringProperty("")


class HistorySessionCard(MDBoxLayout):
    screen = ObjectProperty(None)
    session = ObjectProperty(allownone=True)

    def on_kv_post(self, base_widget):
        container = self.ids.history_items_container
        container.clear_widgets()
        if not self.session:
            return
        for ex in self.session.get("exercises", []):
            name = ex.get("exerciseName", f"#{ex.get('exerciseId')}")
            parts = []
            for s in ex.get("sets", []):
                if s.get("type") == "normal":
                    reps = str(s.get("reps", ""))
                    w = str(s.get("weight", ""))
                    parts.append(f"{reps}x{w}кг")
            container.add_widget(
                HistoryExerciseItem(
                    exercise_name=name,
                    sets_summary=", ".join(parts),
                )
            )


class HistoryScreen(MDScreen):
    def on_enter(self, *args):
        Clock.schedule_once(self.render_workout_history, 0)

    def _history_container(self):
        return self.ids.full_history_container

    def render_workout_history(self, *args):
        container = self._history_container()
        container.clear_widgets()

        try:
            history = _logic().list_workout_history()
        except AttributeError:
            try:
                history = _logic().storage.get().get("workoutHistory", [])
            except Exception:
                history = []

        if not history:
            container.add_widget(
                MDLabel(
                    text="История пуста",
                    halign="center",
                    theme_text_color="Secondary",
                )
            )
            return

        history_sorted = sorted(history, key=lambda s: s.get("date", ""), reverse=True)

        for session in history_sorted:
            card = HistorySessionCard(screen=self, session=session)
            container.add_widget(card)

    def delete_history_session(self, session_id):
        if not session_id:
            return
        _logic().delete_history_session(int(session_id))
        
        Clock.schedule_once(self.render_workout_history, 0)
