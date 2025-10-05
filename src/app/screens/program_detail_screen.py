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
    # Ссылка на родительский экран для вызова методов (например, удаления)
    screen = ObjectProperty(None)
    
    
class ProgramDetailScreen(MDScreen):
    program_id = ObjectProperty(None)
    # exercises = ListProperty([])
    
    def on_enter(self, *args):
        '''
        Вызывается при входе на экран, загружает данные о программе
        '''
        if self.program_id:
            self.load_program_data()
    
    def load_program_data(self):
        '''
        Загружает и отображает данные для программы с текущим program_id
        '''
        app = MDApp.get_running_app()
        # self.program_id = program_id
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
        '''
        Отображает список упражнений
        '''
        container = self.ids.exercise_list
        container.clear_widgets()
        if not self.exercises:
            # добавить заглушку
            pass
        else:
            for ex in self.exercises:
                item = ExerciseItem(exercise_id=ex['id'], exercise_name=ex['name'], screen=self)
                container.add_widget(item)
            
    def add_exercise(self):
        '''
        Добавляет новое упражнение в текущую программу
        '''
        # app = MDApp.get_running_app()
        name = self.ids.new_exercise_name.text.strip()
        if name and self.program_id:
            app = MDApp.get_running_app()
            app.logic.add_exercise_to_program(name)
            self.ids.new_exercise_name.text = ""
            # self.render_exercises_for_active_program()
            #app.root.get_screen('workout').render_todays_workout()
            self.load_program_data()
        
    def delete_exercise(self, exercise_id):
        '''
        Удаляет упражнение из текущей программы
        '''
        if self.program_id:
            app = MDApp.get_running_app()
            app.logic.delete_exercise(exercise_id)
            # self.render_exercises_for_active_program()
            self.load_program_data()
            #app.root.get_screen('workout').render_todays_workout()
    
    def start_workout(self):
        '''
        Запускает тренировку по текущей программе
        '''
        if self.program_id:
            app = MDApp.get_running_app()
            app.logic.select_program(self.program_id)
            # Здесь можно переключить пользователя на экран тренировки
            # print(f"Starting workout for program {self.program_id}")
            # # app.root.current = 'workout_screen'
            # if self.manager:
            #     self.manager.transition.direction = 'right'
            #     self.manager.current = 'workout_screen'
            app.switch_to_workout_screen()
    
    def go_back(self):
        """
        Возвращает пользователя на экран списка программ.
        """
        # Устанавливаем направление перехода для красивой анимации
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = 'programs_screen'
    