
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivymd.uix.swiper import MDSwiperItem

class ProgramSwiperItem(MDSwiperItem):
    program_id = ObjectProperty(None)
    program_name = StringProperty('')
    
class ProgramCard(MDBoxLayout):
    screen = ObjectProperty(None)
    program_id = ObjectProperty(None)
    program_name = StringProperty('')
    progression_type = StringProperty('')
    is_active = ObjectProperty(False)
    
class ExerciseItem(MDBoxLayout):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty('')
    screen = ObjectProperty(None)

class NewProgramDialog(MDDialog):

    def __init__(self, screen, **kwargs):
        super().__init__(**kwargs)
        
        self.screen = screen
        self.prog_map_display = {
            'linear': 'линейная (5x5)',
            'double': 'двойная (3x6-10)',
            'rep_range': 'диапазон (3x8-12)'
        }
        # по дефолту двойная прогрессиия
        self.selected_prog_type = 'double'
    
    def open_menu(self, button):
        """
        Когда MDTextButton нажата открывается и вызывается MDDropdownMenu
        """
        menu_items = [
            {
                "text": display_text,
                "on_release": lambda x=value, y=display_text: self.set_item(x, y),
            } for value, display_text in self.prog_map_display.items()
        ]

        # создаем и открываем меню
        MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        ).open()

    def set_item(self, value, display_text):
        """
        This is the callback function for when a menu item is selected.
        """
        self.selected_prog_type = value
        # self.content_cls.ids.progression_type_button.text = display_text
        self.ids.progression_type_button_text.text = display_text
        # The MDDropdownMenu automatically closes itself, so no need to call dismiss() here.
    
    def create_program(self, *args):
        """
        Создает программу с названием из text field и выбранным типом прогрессии
        """
        # prog_name = self.content_cls.ids.new_program_name_input.text.strip()
        prog_name = self.ids.new_program_name_input.text.strip()
        
        if prog_name:
            app = MDApp.get_running_app()
            app.logic.create_new_program(prog_name, self.selected_prog_type)
            self.screen.render_all()
            self.dismiss()
        

class ProgramsScreen(MDScreen):
    
    new_program_dialog = None
    
    def on_enter(self, *args):
        self.render_all()
        # self.populate_swiper()
    
    def render_all(self):
        """
        Рендерит лист программ и упражнения для активной программы
        """
        self.render_program_list()
        self.render_exercises_for_active_program()
        
    def render_program_list(self):
        """
        Динамически создает ProgramCard виджеты
        """
        app = MDApp.get_running_app()
        container = self.ids.program_list
        container.clear_widgets()
        
        active_id = app.logic.app_data.get('activeProgramId')
        programs = app.logic.app_data.get('workoutPrograms', [])
        
        if programs:
            for program in programs:
                card = ProgramCard(
                    program_id=program['id'],
                    program_name=program['name'],
                    progression_type=program['progressionType'],
                    is_active=(program['id'] == active_id),
                    screen=self
                )
                container.add_widget(card)
                
    def select_program(self, program_id):
        app = MDApp.get_running_app()
        if app.logic.app_data.get('activeProgramId') != program_id:
            app.logic.select_program(program_id)
            self.render_all()
            #app.root.get_screen('workout').render_todays_workout()
    
    def delete_program(self, program_id):
        app = MDApp.get_running_app()
        if app.logic.delete_program(program_id):
            self.render_all()
            #app.root.get_screen('workout').render_todays_workout()

    def render_exercises_for_active_program(self):
        app = MDApp.get_running_app()
        container = self.ids.exercise_list
        container.clear_widgets()
        
        active_program = app.logic.get_active_program()
        if not active_program:
            self.ids.exercises_section.opacity = 0
            self.ids.exercises_section.size_hint_y = None
            self.ids.exercises_section.height = 0
            return

        self.ids.exercises_section.opacity = 1
        self.ids.exercises_section.size_hint_y = None
        self.ids.exercises_section.height = self.ids.exercises_section.minimum_height
        self.ids.active_program_name.text = active_program['name']
        
        if active_program.get('exercises'):
            for ex in active_program['exercises']:
                item = ExerciseItem(
                    exercise_id=ex['id'],
                    exercise_name=ex['name'],
                    screen=self
                )
                container.add_widget(item)

    def add_exercise_to_program(self):
        app = MDApp.get_running_app()
        name = self.ids.new_exercise_name.text.strip()
        if name:
            app.logic.add_exercise_to_program(name)
            self.ids.new_exercise_name.text = ""
            self.render_exercises_for_active_program()
            #app.root.get_screen('workout').render_todays_workout()
        

    def delete_exercise(self, exercise_id):
        app = MDApp.get_running_app()
        app.logic.delete_exercise(exercise_id)
        self.render_exercises_for_active_program()
        #app.root.get_screen('workout').render_todays_workout()
    
    def show_new_program_dialog(self):
        """
        Открывает диалоговое окно для создания новой программы
        """
        if not self.new_program_dialog:
            self.new_program_dialog = NewProgramDialog(screen=self)
        self.new_program_dialog.open()
    
