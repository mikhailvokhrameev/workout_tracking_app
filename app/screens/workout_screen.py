from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock
from kivymd.uix.expansionpanel import MDExpansionPanel
from kivymd.uix.behaviors import RotateBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.list import MDListItemTrailingIcon


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
    def on_enter(self, *args):
        Clock.schedule_once(self.render_todays_workout)

    def render_todays_workout(self, *args):
        logic = MDApp.get_running_app().logic
        container = self.ids.today_workout_container
        container.clear_widgets()

        active_program = logic.get_active_program()

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

    def save_workout(self):
        logic = MDApp.get_running_app().logic

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
            self.manager.current = 'history_screen'