from kivymd.app import MDApp
from kivy.core.text import LabelBase
from kivy.app import Builder
from kivy.core.window import Window
from app.logic.progressive_overload_logic import ProgressiveOverloadLogic 

from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.label import MDLabel
from app.screens.programs_screen import ProgramsScreen, NewProgramDialog, ProgramCard
from app.screens.program_detail_screen import ProgramDetailScreen, ExerciseItem
from app.screens.main_screen import MainScreen
from app.screens.history_screen import HistoryScreen
from app.screens.workout_screen import WorkoutScreen
from components import BaseMDNavigationItem
from components import ProgramsPlaceholder
from kivy.clock import Clock

Window.size = (400, 750)

class MainApp(MDApp):
    def build(self):
        self.logic = ProgressiveOverloadLogic()
        # тема
        self.theme_cls.theme_style = "Light"
        # цвет для кнопок, активных элементов и т.д
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_file('src/app/kv/main_screen.kv')
    
    def on_start(self):
        """
        Вызывается после загрузки всех виджетов
        """
        self.root.ids.screen_manager.current = 'programs_screen'
    
    def on_switch_tabs(
        self,
        bar: MDNavigationBar,
        item: MDNavigationItem,
        item_icon: str,
        item_text: str,
    ):
        '''
        Вызывается при нажатии на элемент нижней навигации. Переключает экран в MDScreenManager
        '''
        self.root.ids.screen_manager.current = item.name
        
    def switch_to_workout_screen(self):
        """
        Программно переключает приложение на экран тренировки.
        """
        # 1. Переключаем экран в ScreenManager
        self.root.ids.screen_manager.current = 'workout_screen'
        
        # 2. Активируем нужную вкладку в навигационной панели
        nav_bar = self.root.ids.nav_bar
        # Находим виджет вкладки по его имени
        workout_item = next((widget for widget in nav_bar.children if hasattr(widget, 'name') and widget.name == 'workout_screen'), None)
        if workout_item:
            nav_bar.set_active_item(workout_item)

    
if __name__ == '__main__':
    MainApp().run()