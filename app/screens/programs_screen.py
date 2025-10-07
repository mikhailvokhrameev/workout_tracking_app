from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.clock import Clock
    
class ProgramCard(MDCard):
    screen = ObjectProperty(None)
    program_id = ObjectProperty(None)
    program_name = StringProperty('')
    progression_type = StringProperty('')


class NewProgramDialog(MDDialog):

    def __init__(self, screen, **kwargs):
        super().__init__(**kwargs)
        
        self.screen = screen
        self.prog_map_display = {
            'linear': 'линейная (5x5)',
            'double': 'двойная (3x6-10)',
            'rep_range': 'диапазон (3x8-12)'
        }
        self.selected_prog_type = 'double'
        
    def on_open(self):
        self.ids.progression_type_button_text.text = self.prog_map_display[self.selected_prog_type]

    
    def open_menu(self, button):
        """Когда MDTextButton нажата открывается и вызывается MDDropdownMenu"""
        menu_items = [
            {
                "text": display_text,
                "on_release": lambda x=value, y=display_text: self.set_item(x, y),
            } for value, display_text in self.prog_map_display.items()
        ]
        
        MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        ).open()

    def set_item(self, value, display_text):
        self.selected_prog_type = value
        self.ids.progression_type_button_text.text = display_text
    
    def create_program(self, *args):
        """Создает программу с названием из text field и выбранным типом прогрессии"""
        prog_name = self.ids.new_program_name_input.text.strip()
        
        if prog_name:
            app = MDApp.get_running_app()
            app.logic.create_new_program(prog_name, self.selected_prog_type)
            Clock.schedule_once(self.screen.populate_program_list)
            self.dismiss()
        

class ProgramsScreen(MDScreen):
    
    new_program_dialog = None
    
    def on_enter(self, *args):
        '''Вызывается при каждом входе на экран'''
        self.populate_program_list()
    
    def open_program_detail(self, program_id):
        '''Переключает на экран деталей программы'''
        if program_id:
            app = MDApp.get_running_app()
            app.logic.app_data['activeProgramId'] = program_id
            app.logic.save_data()
            
            detail_screen = self.manager.get_screen('program_detail')
            detail_screen.program_id = program_id
            self.manager.transition.direction = 'left'
            self.manager.current = 'program_detail'
        
    def populate_program_list(self, *args):
        """Заполняет MDList карточками программ"""
        container = self.ids.program_list
        container.clear_widgets()
        
        app = MDApp.get_running_app()
        programs = app.logic.app_data.get('programs', [])

        if programs:
            for program in programs:
                card = ProgramCard(
                    screen=self,
                    program_id=program['id'],
                    program_name=program['name'],
                    progression_type=program['progressionType']
                )
                container.add_widget(card)
                
    def delete_program(self, program_id):
        app = MDApp.get_running_app()
        if app.logic.delete_program(program_id):
            self.populate_program_list()
    
    def show_new_program_dialog(self):
        """Открывает диалоговое окно для создания новой программы"""
        if not self.new_program_dialog:
            self.new_program_dialog = NewProgramDialog(screen=self)
        self.new_program_dialog.open()
        
