from kivymd.app import MDApp
from kivy.core.text import LabelBase
from kivy.app import Builder
from kivy.core.window import Window
from app.logic.progressive_overload_logic import ProgressiveOverloadLogic 

from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.label import MDLabel

from app.screens.main_screen import MainScreen
from app.screens.history_screen import HistoryScreen
from app.screens.programs_screen import ProgramsScreen
from components import BaseMDNavigationItem
from components import ProgramsPlaceholder

Window.size = (400, 750)
LabelBase.register(name='Montserrat', fn_regular='src/app/assets/fonts/Montserrat-Regular.ttf', fn_bold='src/app/assets/fonts/Montserrat-Bold.ttf')

class MainApp(MDApp):
    def build(self):
        self.logic = ProgressiveOverloadLogic()
        # тема
        self.theme_cls.theme_style = "Light"
        # цвет для кнопок, активных элементов и т.д
        self.theme_cls.primary_palette = "Blue"
        MDLabel.font_name = 'Montserrat'
        return Builder.load_file('src/app/kv/main_screen.kv')
    
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

    
if __name__ == '__main__':
    MainApp().run()