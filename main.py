import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy_garden.graph import Graph, LinePlot
from kivy.uix.label import Label # placeholder text
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.window import Window
from kivy.core.text import LabelBase # for font registration
from progressive_overload_logic import ProgressiveOverloadLogic 

# mobile-like window size for desktop testing
Window.size = (400, 750)

# font registration
LabelBase.register(name='Montserrat', fn_regular='fonts/Montserrat-Regular.ttf', fn_bold='fonts/Montserrat-Bold.ttf')

class FormGroup(BoxLayout):
    """
    A custom widget that holds a label and another input widget.
    This class defines the 'label_text' property so it can be used in the .kv file
    """
    label_text = StringProperty('')

class SummaryModal(ModalView):
    """
    Workout summary popup
    """
    app = ObjectProperty(None)

class StagnationModal(ModalView):
    """
    Stagnation/regress popup
    """
    app = ObjectProperty(None)

class NewProgramModal(ModalView):
    app = ObjectProperty(None)


class MainScreen(BoxLayout):
    """
    This is the root widget of the application
    It holds references to all UI elements and handles the application's flow
    """
    app = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        # this should only initialize the widget's internal variables
        self.logic = ProgressiveOverloadLogic()
        self.summary_modal = None
        self.stagnation_modal = None
        super().__init__(**kwargs)
        # this will map the text in the spinner to the actual exercise ID
        self.exercise_spinner_map = {}

    def handle_tab_switch(self, tab):
        """
        This function is the place where tab content is rendered.
        It is called automatically on startup for the default tab, and
        it's called whenever the user clicks a different tab
        """
        tab_text = tab.text
        if tab_text == 'Тренировка':
            self.render_todays_workout()
        elif tab_text == 'Программы':
            self.render_program_list()
            self.render_exercises_for_active_program()
        elif tab_text == 'История':
            self.render_workout_history()
        elif tab_text == 'Графики':
            self.render_graph_view()
    
    def add_new_program(self, program_name, progression_type_text):
        """
        Callback from a dialog to add a new program
        """
        prog_map = {
            'Линейная (5x5)': 'linear',
            'Двойная (3x6-10)': 'double',
            'Диапазон (3x8-12)': 'rep_range'
        }
        prog_type = prog_map.get(progression_type_text, 'double')
        self.logic.create_new_program(program_name, prog_type)
        self.render_program_list()
    
    def show_new_program_dialog(self):
        # create an instance of the modal and open it
        modal = NewProgramModal(app=self.app)
        modal.open()
    
    def render_all_screens(self):
        """
        safely renders the content for all parts of the UI
        """
        try:
            self.render_todays_workout()
        except KeyError:
            pass
        try:
            self.render_program_list()
            self.render_exercises_for_active_program()
        except KeyError:
            pass
        try:
            self.render_workout_history()
        except KeyError:
            pass

    def render_program_list(self):
        """
        dynamically creates ProgramCard widgets
        """
        container = self.ids.program_list
        container.clear_widgets()
        
        active_id = self.logic.app_data['activeProgramId']
        
        if not self.logic.app_data['programs']:
            self.ids.program_list_placeholder.opacity = 1
        else:
            self.ids.program_list_placeholder.opacity = 0
            for program in self.logic.app_data['programs']:
                card = ProgramCard(
                    program_id=program['id'],
                    program_name=program['name'],
                    progression_type=program['progressionType'],
                    is_active=program['id'] == active_id,
                    main_screen=self
                )
                container.add_widget(card)

    def select_program(self, program_id):
        if self.logic.app_data['activeProgramId'] != program_id:
            self.logic.select_program(program_id)
            self.render_all_screens()
    
    def delete_program(self, program_id):
        if self.logic.delete_program(program_id):
            self.render_all_screens()

    def render_exercises_for_active_program(self):
        container = self.ids.exercise_list
        container.clear_widgets()
        
        active_program = self.logic.get_active_program()
        if not active_program:
            self.ids.exercises_section.opacity = 0
            self.ids.exercises_section.height = 0
            return

        self.ids.exercises_section.opacity = 1
        self.ids.exercises_section.height = self.ids.exercises_section.minimum_height
        self.ids.active_program_name.text = active_program['name']
        
        if not active_program['exercises']:
            self.ids.exercise_placeholder.opacity = 1
        else:
            self.ids.exercise_placeholder.opacity = 0
            for ex in active_program['exercises']:
                item = ExerciseItem(
                    exercise_id=ex['id'],
                    exercise_name=ex['name'],
                    main_screen=self
                )
                container.add_widget(item)

    def add_exercise_to_program(self):
        name = self.ids.new_exercise_name.text.strip()
        if name:
            self.logic.add_exercise_to_program(name)
            self.ids.new_exercise_name.text = ""
            self.render_exercises_for_active_program()
            self.render_todays_workout()

    def delete_exercise(self, exercise_id):
        self.logic.delete_exercise(exercise_id)
        self.render_exercises_for_active_program()
        self.render_todays_workout()

    def render_todays_workout(self):
        container = self.ids.today_workout_container
        container.clear_widgets()

        active_program = self.logic.get_active_program()
        if not active_program or not active_program['exercises']:
            self.ids.workout_placeholder.opacity = 1
            self.ids.save_workout_btn.disabled = True
            return

        self.ids.workout_placeholder.opacity = 0
        self.ids.save_workout_btn.disabled = False

        for ex in active_program['exercises']:
            last_workout = ex['history'][-1] if ex['history'] else None
            last_workout_text = "Это первая тренировка!"
            if last_workout:
                sets_str = ", ".join([f"{s['reps']}x{s['weight']}кг" for s in last_workout['sets']])
                last_workout_text = f"Прошлая: {sets_str}"

            target_text = "Цель: Выполните рабочие подходы."
            if ex.get('nextTarget'):
                target = ex['nextTarget']
                target_text = f"Цель: {target['text']} с весом ~[b]{target['weight']} кг[/b]"

            card = ExerciseWorkoutCard(
                exercise_id=ex['id'],
                exercise_name=ex['name'],
                target_info=target_text,
                last_workout_info=last_workout_text,
                main_screen=self
            )
            
            # add existing sets from current_workout_state
            for s in self.logic.current_workout_state.get(ex['id'], []):
                card.add_set_row(set_data=s)
            
            container.add_widget(card)

    def save_workout(self):
        # First, update the logic state from the UI inputs
        for exercise_card in self.ids.today_workout_container.children:
            if isinstance(exercise_card, ExerciseWorkoutCard):
                for set_row in exercise_card.ids.new_sets_container.children:
                    self.logic.update_set_in_workout(
                        set_row.exercise_id,
                        set_row.set_id,
                        'weight',
                        set_row.ids.weight_input.text
                    )
                    self.logic.update_set_in_workout(
                        set_row.exercise_id,
                        set_row.set_id,
                        'reps',
                        set_row.ids.reps_input.text
                    )

        summary_result = self.logic.save_workout()
        
        if summary_result:
            self.show_summary_modals(summary_result)
            self.render_all_screens()
            self.ids.tabs.switch_to(self.ids.history_tab)
            # After saving, always refresh the graph data
            self.render_graph_view()
        else:
            # !!!Add here a popup saying "No data entered"!!!
            pass

    def show_summary_modals(self, summary):
        if summary['all_goals_achieved']:
            if not self.summary_modal:
                self.summary_modal = SummaryModal(app=self.app)
            
            content_text = ""
            for detail in summary['details']:
                content_text += f"[b]{detail['exercise_name']}:[/b] {detail['message']}\n{detail['next_target_text']}\n\n"
            content_text += "Отличная работа! Цели на следующую тренировку обновлены."
            
            self.summary_modal.ids.summary_content.text = content_text
            self.summary_modal.open()
        else:
            if not self.stagnation_modal:
                self.stagnation_modal = StagnationModal(app=self.app)
            self.stagnation_modal.open()

    def render_workout_history(self):
        container = self.ids.full_history_container
        container.clear_widgets()

        history = self.logic.app_data.get('workoutHistory', [])
        if not history:
            self.ids.history_placeholder.opacity = 1
            return
        
        self.ids.history_placeholder.opacity = 0
        for session in reversed(history):
            card = HistorySessionCard(session=session, main_screen=self)
            container.add_widget(card)
    
    def delete_history_session(self, session_id):
        """
        Deletes a single workout session from history
        """
        if session_id: # safety check
            self.logic.delete_history_session(session_id)
            self.render_workout_history()
            # refresh the graph data after deleting
            self.render_graph_view()

    def confirm_reset_all_data(self):
        """
        This function is called by the 'reset all data' button.
        It creates and shows the popup window
           """
        modal = ResetConfirmationModal(app=self.app)
        modal.open()

    def execute_reset_all_data(self):
        """
        This function is called by the 'Yes, delete' button inside the popup.
        It performs the actual deletion and resets the UI
        """
        self.logic.reset_all_data()
        
        # safely reset the view to the default tab
        default_tab = self.ids.tabs.tab_list[-1]
        self.handle_tab_switch(default_tab)
        self.ids.tabs.switch_to(default_tab)
    
    def render_graph_view(self):
        """
        This function should be called whenever the data might have changed
        """
        pass # !!!You need to write a function for graphs!!!

    def on_graph_spinner_select(self, selected_text):
        """
        Called when the user selects an exercise from the Spinner in the Graphs tab
        """
        pass # !!!You need to write a function for graphs!!!

    def draw_exercise_graph(self, exercise_id):
        """
        Gets the 1RM data from the logic and draws the actual graph
        """
        pass # !!!You need to write a function for graphs!!!

# custom widgets for dynamic content

class ProgramCard(ButtonBehavior, BoxLayout):
    program_id = ObjectProperty(None)
    program_name = StringProperty('')
    progression_type = StringProperty('')
    is_active = ObjectProperty(False)
    main_screen = ObjectProperty(None)

class ExerciseItem(BoxLayout):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty('')
    main_screen = ObjectProperty(None)

class ExerciseWorkoutCard(BoxLayout):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty('')
    target_info = StringProperty('')
    last_workout_info = StringProperty('')
    main_screen = ObjectProperty(None)

    def add_set_row(self, set_data=None):
        exercise_id = self.exercise_id
        if set_data: # re-rendering an existing set
            set_id = set_data['id']
            weight = str(set_data['weight'])
            reps = str(set_data['reps'])
        else: # adding a new set
            self.main_screen.logic.add_set_to_workout(exercise_id)
            new_set = self.main_screen.logic.current_workout_state[exercise_id][-1]
            set_id = new_set['id']
            weight, reps = '', ''

        set_row = NewSetRow(
            exercise_id=exercise_id,
            set_id=set_id,
            weight=weight,
            reps=reps,
            card_ref=self
        )
        self.ids.new_sets_container.add_widget(set_row)
    
    def remove_set_row(self, set_row):
        self.main_screen.logic.delete_set_from_workout(set_row.exercise_id, set_row.set_id)
        self.ids.new_sets_container.remove_widget(set_row)

class NewSetRow(BoxLayout):
    exercise_id = ObjectProperty(None)
    set_id = ObjectProperty(None)
    weight = StringProperty('')
    reps = StringProperty('')
    card_ref = ObjectProperty(None)

class HistorySessionCard(BoxLayout):
    session = ObjectProperty(None)
    main_screen = ObjectProperty(None)

    def on_session(self, instance, value):
        # When the session data arrives, don't populate immediately
        # Instead, schedule the _populate_content function to run on the next frame
        Clock.schedule_once(self._populate_content)

    def _populate_content(self, dt):
        """
        This function runs after the widget has been fully built,
        so self.ids is now guaranteed to be available
        """
        
        container = self.ids.history_items_container
        container.clear_widgets()
        
        # .get() for safety in case of corrupted data
        for ex in self.session.get('exercises', []):
            sets_string = ", ".join([f"{s['reps']}x{s['weight']}кг" for s in ex.get('sets', [])])
            item_text = f"[b]{ex.get('exerciseName', 'Unknown')}:[/b] {sets_string}"
            item = HistoryItemLabel(text=item_text)
            container.add_widget(item)

class HistoryItemLabel(BoxLayout):
    text = StringProperty('')

class ResetConfirmationModal(ModalView):
    app = ObjectProperty(None)


class MainApp(App):
    def build(self):
        from kivy.uix.label import Label
        Label.font_name = 'Montserrat'
        return MainScreen(app=self)

if __name__ == '__main__':
    MainApp().run()