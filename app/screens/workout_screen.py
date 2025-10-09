from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, StringProperty
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
    MDDialogContentContainer
)
from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel


class WorkoutSummaryContent(MDBoxLayout):
    summary_text = StringProperty("")

class NewSetRow(MDBoxLayout):
    """Виджет для одного сета упражнения"""
    exercise_id = ObjectProperty(None)
    set_id = ObjectProperty(None)
    weight = StringProperty('')
    reps = StringProperty('')
    panel_ref = ObjectProperty(None)
    
class TrailingPressedIconButton(
    ButtonBehavior, RotateBehavior, MDListItemTrailingIcon
):
    pass
    
class ExpansionPanelItem(MDExpansionPanel):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty('')
    target_info = StringProperty('')
    last_workout_info = StringProperty('')

    def on_open(self, *args):
        self.add_set_row()
    

    def add_set_row(self, set_data=None):
        logic = MDApp.get_running_app().logic
        exercise_id = self.exercise_id

        if set_data:
            set_id = set_data['id']
            weight = str(set_data['weight'])
            reps = str(set_data['reps'])
        else:
            logic.add_set_to_workout(exercise_id)
            new_set = logic.current_workout_state[exercise_id][-1]
            set_id = new_set['id']
            weight, reps = '', ''

        set_row = NewSetRow(
            exercise_id=exercise_id,
            set_id=set_id,
            weight=weight,
            reps=reps,
            panel_ref=self
        )
        self.ids.new_sets_container.add_widget(set_row)
        

    def remove_set_row(self, set_row):
        logic = MDApp.get_running_app().logic
        logic.delete_set_from_workout(set_row.exercise_id, set_row.set_id)
        self.ids.new_sets_container.remove_widget(set_row)


class WorkoutScreen(MDScreen):
    dialog = None
    
    def on_enter(self, *args):
        Clock.schedule_once(self.render_todays_workout)

    def render_todays_workout(self, *args):
        logic = MDApp.get_running_app().logic
        container = self.ids.today_workout_container
        container.clear_widgets()

        active_program = logic.get_active_program()
        
        if not active_program:
            # Отображаем заглушку или сообщение о необходимости создать программу
            placeholder = MDLabel(
                text= "Нет активной программы",
                halign="center",
                theme_text_color="Secondary"
            )
            container.add_widget(placeholder)
            return
        
        for ex in active_program['exercises']:
            last_workout = ex['history'][-1] if ex['history'] else None
            last_workout_text = "Это первая тренировка!"
            if last_workout:
                sets_str = ", ".join([f"{s['reps']}x{s['weight']}кг" for s in last_workout['sets']])
                last_workout_text = f"Прошлая: {sets_str}"

            target_text = "Выполните рабочие подходы"
            if ex.get('nextTarget'):
                target = ex['nextTarget']
                target_text = f"Цель: {target['text']} с весом ~[b]{target['weight']} кг[/b]"

            panel = ExpansionPanelItem(
                exercise_id=ex['id'],
                exercise_name=ex['name'],
                target_info=target_text,
                last_workout_info=last_workout_text
            )

            for s in logic.current_workout_state.get(ex['id'], []):
                panel.add_set_row(set_data=s)

            container.add_widget(panel)
    
    def _collect_ui_data(self):
        logic = MDApp.get_running_app().logic
        for panel in reversed(self.ids.today_workout_container.children):
            if isinstance(panel, ExpansionPanelItem):
                for set_row in panel.ids.new_sets_container.children:
                    logic.update_set_in_workout(
                        set_row.exercise_id, set_row.set_id,
                        'weight', set_row.ids.weight_input.text
                    )
                    logic.update_set_in_workout(
                        set_row.exercise_id, set_row.set_id,
                        'reps', set_row.ids.reps_input.text
                    )

    def show_save_confirmation_dialog(self):
        app = MDApp.get_running_app()
        self._collect_ui_data()

        active_program = app.logic.get_active_program()
        if not active_program:
            print("No active program found.")
            return

        saved_exercises_data = []
        
        for exercise in active_program['exercises']:
            exercise_id = exercise['id']
 
            workout_sets = app.logic.current_workout_state.get(exercise_id, [])
            
            sets_to_save = []
            for s in workout_sets:
                if str(s.get('weight', '')).strip() and str(s.get('reps', '')).strip():
                    try:
                        sets_to_save.append({
                            **s,
                            'weight': float(s['weight']),
                            'reps': int(s['reps'])
                        })
                    except (ValueError, TypeError):
                        continue
            
            if sets_to_save:
                last_history = exercise['history'][-1] if exercise['history'] else None
                
                exercise_with_program = {**exercise, 'programId': active_program['id']}
                
                saved_exercises_data.append({
                    'exercise': exercise_with_program,
                    'newSets': sets_to_save,
                    'lastHistory': last_history
                })
        
        if not saved_exercises_data:
            print("No valid sets recorded to save.")
            return
        
        summary_data = app.logic.generate_workout_summary(saved_exercises_data)
    
        final_text = ""
        if not summary_data['all_goals_achieved']:
            final_text += "Ничего страшного!\n"
            final_text += "Результаты оказались чуть ниже. Это нормально. Главное — не сдаваться!\n\n"

        final_text += "[b]Детали прогресса:[/b]\n\n"
        for detail in summary_data['details']:
            final_text += f"{detail['exercise_name']}: {detail['message']}\n"
            final_text += f"{detail['next_target_text']}\n\n"
       
        if not self.dialog:
            content = WorkoutSummaryContent(summary_text=final_text)
            
            self.dialog = MDDialog(
                MDDialogHeadlineText(
                    text="Сохранить тренировку?",
                    halign="center"
                ),
                MDDialogContentContainer(
                    content,
                    orientation='vertical',
                ),
                MDDialogButtonContainer(
                    Widget(),
                    MDButton(MDButtonText(text="Отмена"), style="text", on_release=self.close_dialog),
                    MDButton(MDButtonText(text="Сохранить"), style="text", on_release=self.save_and_close_dialog),
                    spacing="4dp",
                ),
                size_hint_x=0.9,
                auto_dismiss=False,
            )

        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def save_workout(self):
        logic = MDApp.get_running_app().logic
        app = MDApp.get_running_app()

        for panel in self.ids.today_workout_container.children:
            if isinstance(panel, ExpansionPanelItem):
                for set_row in panel.ids.new_sets_container.children:
                    logic.update_set_in_workout(
                        set_row.exercise_id,
                        set_row.set_id,
                        'weight',
                        set_row.ids.weight_input.text
                    )
                    logic.update_set_in_workout(
                        set_row.exercise_id,
                        set_row.set_id,
                        'reps',
                        set_row.ids.reps_input.text
                    )

        summary_result = logic.save_workout()
        if summary_result:
            app.switch_to_screen('history')
        
    # def show_save_confirmation_dialog(self):
    #     """
    #     Диалоговое окно для подтверждения сохранения тренировки
    #     """
    #     if not self.dialog:
    #         self.dialog = MDDialog(
    #             MDDialogHeadlineText(
    #                 text="Сохранить тренировку?",
    #             ),
    #             MDDialogSupportingText(
    #                 text="Вы уверены, что хотите завершить и сохранить эту тренировку?",
    #             ),
    #             MDDialogButtonContainer(
    #                 Widget(),
    #                 MDButton(
    #                     MDButtonText(text="Отмена"),
    #                     style="text",
    #                     on_release=self.close_dialog,
    #                 ),
    #                 MDButton(
    #                     MDButtonText(text="Сохранить"),
    #                     style="text",
    #                     on_release=self.save_and_close_dialog,
    #                 ),
    #                 spacing="8dp",
    #             ),
    #         )
    #     self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def save_and_close_dialog(self, *args):
        app = MDApp.get_running_app()
        self.save_workout()
        self.close_dialog()