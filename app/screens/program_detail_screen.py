# -*- coding: utf-8 -*-

from __future__ import annotations
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock


def _logic():
    return MDApp.get_running_app().logic


class ExerciseItem(MDBoxLayout):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty("")
    screen = ObjectProperty(None)


class ProgramDetailScreen(MDScreen):
    program_id = ObjectProperty(None)
    exercises_cache = None

    def on_enter(self, *args):
        if self.program_id:
            Clock.schedule_once(lambda dt: self.load_program_data(), 0)

    def load_program_data(self):
        if not self.program_id:
            return

        logic = _logic()
        program = logic.get_program_by_id(self.program_id)
        if not program:
            try:
                programs = logic.list_programs()
                program = next((p for p in programs if p.get("id") == self.program_id), None)
            except AttributeError:
                try:
                    programs = logic.storage.get().get("programs", [])
                    program = next((p for p in programs if p.get("id") == self.program_id), None)
                except Exception:
                    program = None

        if program:
            self.ids.program_name.text = program.get("name", "")
            self.exercises_cache = list(program.get("exercises", []))
            self.render_exercises()
        else:
            self.ids.program_name.text = "Программа не найдена"
            self.ids.exercise_list.clear_widgets()
            self.exercises_cache = []

    def render_exercises(self):
        container = self.ids.exercise_list
        container.clear_widgets()

        if not self.exercises_cache:
            return

        for ex in self.exercises_cache:
            item = ExerciseItem(
                exercise_id=ex.get("id"),
                exercise_name=ex.get("name", ""),
                screen=self,
            )
            container.add_widget(item)

    def add_exercise(self):
        name = self.ids.new_exercise_name.text.strip()
        if not name or len(name) > 30 or not self.program_id:
            return
        
        logic = _logic()
        logic.select_program(self.program_id)
        logic.add_exercise_to_program(name)

        self.ids.new_exercise_name.text = ""
        self.load_program_data()

    def delete_exercise(self, exercise_id):
        if not self.program_id or not exercise_id:
            return

        logic = _logic()
        logic.select_program(self.program_id)
        logic.delete_exercise(exercise_id)
        self.load_program_data()

    def start_workout(self):
        if not self.program_id:
            return
        
        logic = _logic()
        logic.select_program(self.program_id)
        MDApp.get_running_app().switch_to_screen("workout")

    def go_back(self):
        if self.manager:
            self.manager.transition.direction = "right"
            self.manager.current = "programs_screen"

    