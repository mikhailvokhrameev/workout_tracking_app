from __future__ import annotations
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock
from kivymd.uix.expansionpanel import MDExpansionPanel
from kivymd.uix.behaviors import RotateBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.list import MDListItemTrailingIcon
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer,
)
from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel


def _logic():
    return MDApp.get_running_app().logic

def _session_snapshot():
    return _logic().get_current_workout_state()


class WorkoutSummaryContent(MDBoxLayout):
    summary_text = StringProperty("")

class NewSetRow(MDBoxLayout):
    exercise_id = ObjectProperty(None)
    set_id = ObjectProperty(None)
    weight = StringProperty('')
    reps = StringProperty('')
    panel_ref = ObjectProperty(None)
    set_number = StringProperty('')
    
    weight_error = BooleanProperty(False)
    reps_error = BooleanProperty(False)
    
    def on_weight(self, instance, value):
        self._validate_and_update('weight', value)

    def on_reps(self, instance, value):
        self._validate_and_update('reps', value)

    def _validate_and_update(self, property_name, value):
        is_valid = True
        try:
            if not value:
                is_valid = True
            elif property_name == 'weight':
                val = float(value)
                if not (0 <= val < 1000):
                    is_valid = False
            elif property_name == 'reps':
                val = int(value)
                if not (0 <= val < 100):
                    is_valid = False
        except (ValueError, TypeError):
            is_valid = False

        target_property = f"{property_name}_error"
        
        setattr(self, target_property, False)
        
        if not is_valid:
            Clock.schedule_once(lambda dt: setattr(self, target_property, True), 0)
            
        logic = _logic()
        logic.update_set_error_state(self.exercise_id, self.set_id, property_name, not is_valid)

    
class TrailingPressedIconButton(ButtonBehavior, RotateBehavior, MDListItemTrailingIcon):
    pass
    

class ExpansionPanelItem(MDExpansionPanel):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty("")
    target_info = StringProperty("")
    last_workout_info = StringProperty("")

    def on_open(self, *args):
        self.add_set_row()

    def add_set_row(self, set_data=None):
        logic = _logic()
        exercise_id = self.exercise_id
        current_sets_count = len(self.ids.new_sets_container.children)
        if current_sets_count >= 5:
            print("Достигнуто ограничение в 5 подходов")
            return

        set_number = str(current_sets_count + 1)

        if set_data:
            set_id = set_data["id"]
            weight = str(set_data.get("weight", ""))
            reps = str(set_data.get("reps", ""))
        else:
            logic.add_set_to_workout(exercise_id)
            sets_for_ex = _session_snapshot().get(exercise_id, [])
            if not sets_for_ex:
                return
            new_set = sets_for_ex[-1]
            set_id = new_set["id"]
            weight, reps = "", ""

        set_row = NewSetRow(
            exercise_id=exercise_id,
            set_id=set_id,
            weight=weight,
            reps=reps,
            panel_ref=self,
        )
        set_row.set_number = set_number
        self.ids.new_sets_container.add_widget(set_row)

    def remove_set_row(self, set_row):
        _logic().delete_set_from_workout(set_row.exercise_id, set_row.set_id)
        self.ids.new_sets_container.remove_widget(set_row)


class WorkoutScreen(MDScreen):
    dialog = None
    pending_workout_data = None

    def on_enter(self, *args):
        Clock.schedule_once(self.render_todays_workout)

    def render_todays_workout(self, *args):
        logic = _logic()
        container = self.ids.today_workout_container
        container.clear_widgets()

        active_program = logic.get_active_program()
        if not active_program:
            placeholder = MDLabel(
                text="Нет активной программы",
                halign="center",
                theme_text_color="Secondary",
            )
            container.add_widget(placeholder)
            return

        snapshot = _session_snapshot()
        for ex in active_program["exercises"]:
            last_workout = ex["history"][-1] if ex.get("history") else None
            last_workout_text = "Это первая тренировка!"
            if last_workout:
                sets_str = ", ".join([f"{s['reps']}x{s['weight']}кг" for s in last_workout.get("sets", [])])
                last_workout_text = f"Прошлая: {sets_str}"

            target_text = "Выполните рабочие подходы"
            if ex.get("nextTarget"):
                target = ex["nextTarget"]
                w = target.get("weight", "")
                w_text = f" с весом ~[b]{w} кг[/b]" if w != "" else ""
                target_text = f"Цель: {target.get('text','')}"+w_text

            panel = ExpansionPanelItem(
                exercise_id=ex["id"],
                exercise_name=ex["name"],
                target_info=target_text,
                last_workout_info=last_workout_text,
            )

            for s in snapshot.get(ex["id"], []):
                panel.add_set_row(set_data=s)

            container.add_widget(panel)

    def _collect_ui_data(self):
        logic = _logic()
        for panel in reversed(self.ids.today_workout_container.children):
            if isinstance(panel, ExpansionPanelItem):
                for set_row in panel.ids.new_sets_container.children:
                    logic.update_set_in_workout(
                        set_row.exercise_id, set_row.set_id, "weight", set_row.ids.weight_input.text
                    )
                    logic.update_set_in_workout(
                        set_row.exercise_id, set_row.set_id, "reps", set_row.ids.reps_input.text
                    )

    def show_save_confirmation_dialog(self):
        logic = _logic()

        if logic.has_validation_errors():
            print("Нельзя сохранить тренировку, есть ошибки в данных.")
            if not self.dialog:
                self.dialog = MDDialog(
                    MDDialogHeadlineText(text="Ошибка"),
                    MDDialogSupportingText(
                        text="Пожалуйста, исправьте некорректные значения веса или повторений"
                    ),
                    MDDialogButtonContainer(
                        MDButton(MDButtonText(text="OK"), style="text", on_release=self.close_dialog),
                        spacing="8dp",
                    ),
                )
            self.dialog.open()
            return

        self._collect_ui_data()

        active_program = logic.get_active_program()
        if not active_program:
            print("Нет активной программы.")
            return

        snapshot = _session_snapshot()
        saved_exercises_data = []
        for exercise in active_program["exercises"]:
            exercise_id = exercise["id"]
            workout_sets = snapshot.get(exercise_id, [])
            sets_to_save = []
            for s in workout_sets:
                if str(s.get("weight", "")).strip() and str(s.get("reps", "")).strip():
                    try:
                        sets_to_save.append(
                            {**s, "weight": float(s["weight"]), "reps": int(s["reps"])}
                        )
                    except (ValueError, TypeError):
                        continue
            if sets_to_save:
                exercise_with_program_id = exercise.copy()
                exercise_with_program_id["programId"] = active_program["id"]
                saved_exercises_data.append(
                    {
                        "exercise": exercise_with_program_id,
                        "newSets": sets_to_save,
                    }
                )

        if not saved_exercises_data:
            print("Нет данных для сохранения.")
            return

        self.pending_workout_data = saved_exercises_data

        summary_data = logic.generate_workout_summary(self.pending_workout_data)
        final_text = ""
        if not summary_data["all_goals_achieved"]:
            final_text += "Ничего страшного! Результаты оказались чуть ниже ожидаемых.\n\n"
        final_text += "[b]Детали прогресса:[/b]\n\n"
        for detail in summary_data["details"]:
            final_text += f"{detail['exercise_name']}: {detail['message']}\n"
            final_text += f"{detail['next_target_text']}\n\n"

        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Сохранить тренировку?"),
            MDDialogContentContainer(
                WorkoutSummaryContent(summary_text=final_text),
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(MDButtonText(text="Отмена"), style="text", on_release=self.close_dialog),
                MDButton(MDButtonText(text="Сохранить"), style="text", on_release=self.save_and_close_dialog),
                spacing="8dp",
            ),
            size_hint_x=0.9,
            auto_dismiss=False,
        )
        self.dialog.open()

    def save_workout(self):
        logic = _logic()

        self._collect_ui_data()

        if logic.has_validation_errors():
            print("Сохранение отменено: есть ошибки валидации.")
            return

        active_program = logic.get_active_program()
        if not active_program:
            print("Нет активной программы для сохранения.")
            return

        snapshot = _session_snapshot()
        saved_exercises_data = []
        for exercise in active_program["exercises"]:
            workout_sets = snapshot.get(exercise["id"], [])
            sets_to_save = []
            for s in workout_sets:
                if str(s.get("weight", "")).strip() and str(s.get("reps", "")).strip():
                    try:
                        sets_to_save.append(
                            {**s, "weight": float(s["weight"]), "reps": int(s["reps"])}
                        )
                    except (ValueError, TypeError):
                        continue
            if sets_to_save:
                exercise_with_program_id = exercise.copy()
                exercise_with_program_id["programId"] = active_program["id"]
                saved_exercises_data.append(
                    {"exercise": exercise_with_program_id, "newSets": sets_to_save}
                )

        if not saved_exercises_data:
            print("Нет сетов для сохранения.")
            return

        logic.save_workout(saved_exercises_data)

        MDApp.get_running_app().switch_to_screen("history")

    def save_and_close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
        if self.pending_workout_data:
            logic = _logic()
            app = MDApp.get_running_app()
            logic.save_workout(self.pending_workout_data)
            self.pending_workout_data = None
            app.switch_to_screen("history")
        else:
            print("Нет данных для сохранения.")

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None