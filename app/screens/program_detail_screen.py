from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.clock import Clock

class ExerciseItem(MDBoxLayout):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty('')
    screen = ObjectProperty(None)
    
    
class ProgramDetailScreen(MDScreen):
    program_id = ObjectProperty(None)
    
    def on_enter(self, *args):
        '''Загружает данные о программе при каждом входе на экран'''
        if self.program_id:
            self.load_program_data()
    
    def load_program_data(self):
        '''Загружает и отображает данные для программы с текущим program_id'''
        app = MDApp.get_running_app()
        # находим программу по id
        program = next((p for p in app.logic.app_data.get('programs', []) if p['id'] == self.program_id), None)
        if program:
            self.ids.program_name.text = program['name']
            self.exercises = program.get('exercises', [])
            self.render_exercises()
        else:
            self.ids.program_name.text = "Программа не найдена"
            self.ids.exercise_list.clear_widgets()
    
    def render_exercises(self):
        '''Отображает список упражнений'''
        container = self.ids.exercise_list
        container.clear_widgets()
        if self.exercises:
            for ex in self.exercises:
                item = ExerciseItem(exercise_id=ex['id'], exercise_name=ex['name'], screen=self)
                container.add_widget(item)
            
    def add_exercise(self):
        '''Добавляет новое упражнение в текущую программу'''
        name = self.ids.new_exercise_name.text.strip()
        if name and self.program_id:
            app = MDApp.get_running_app()
            app.logic.add_exercise_to_program(name)
            self.ids.new_exercise_name.text = ""
            self.load_program_data()
        
    def delete_exercise(self, exercise_id):
        '''Удаляет упражнение из текущей программы'''
        if self.program_id:
            app = MDApp.get_running_app()
            app.logic.delete_exercise(exercise_id)
            self.load_program_data()
    
    def start_workout(self):
        '''Запускает тренировку по текущей программе'''
        if self.program_id:
            app = MDApp.get_running_app()
            app.logic.select_program(self.program_id)
            app.switch_to_workout_screen()
    
    def go_back(self):
        """Возвращает на экран списка программ"""
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = 'programs_screen'
    