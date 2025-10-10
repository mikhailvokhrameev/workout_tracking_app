from kivymd.app import MDApp
from kivy.app import Builder
from kivy.core.window import Window
from app.logic.progressive_overload_logic import ProgressiveOverloadLogic 
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.label import MDLabel
from app.screens.programs_screen import ProgramsScreen, NewProgramDialog, ProgramCard
from app.screens.program_detail_screen import ProgramDetailScreen, ExerciseItem
from app.screens.main_screen import MainScreen
from app.screens.history_screen import HistoryScreen
from app.screens.workout_screen import WorkoutScreen, NewSetRow, TrailingPressedIconButton, ExpansionPanelItem, WorkoutScreen
from app.screens.graph_screen import GraphScreen
from app.logic.components import BaseMDNavigationItem
from app.logic.components import SettingsTopAppBar
from kivy.clock import Clock
from kivymd.uix.expansionpanel import MDExpansionPanel
from app.screens.workout_screen import TrailingPressedIconButton 
from kivy.metrics import dp
from kivymd.uix.expansionpanel import MDExpansionPanel
from app.screens.progressive_overload_screen import ProgressiveOverloadScreen


Window.size = (400, 750)

class MainApp(MDApp):
    def build(self):
        self.logic = ProgressiveOverloadLogic()
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_file('app/kv/main_screen.kv')
    
    def on_start(self):
        self.root.ids.screen_manager.current = 'programs_screen'
    
    def on_switch_tabs(
        self,
        bar: MDNavigationBar,
        item: MDNavigationItem,
        item_icon: str,
        item_text: str,
    ):
        self.root.ids.screen_manager.current = item.name

    def switch_to_screen(self, screen_name):
        self.root.ids.screen_manager.current = f'{screen_name}_screen'
    
        nav_bar = self.root.ids.nav_bar
        item = next((widget for widget in nav_bar.children if hasattr(widget, 'name') and widget.name == f'{screen_name}_screen'), None)
        if item:
            nav_bar.set_active_item(item)
        
    def tap_expansion_chevron(
        self, panel: MDExpansionPanel, chevron: TrailingPressedIconButton
    ):
        if panel.is_open:
            panel.close()
            panel.set_chevron_up(chevron)
        else:
            panel.open()
            panel.set_chevron_down(chevron)
            
    def reset_all_data(self):
        self.logic.reset_all_data()
        self.root.ids.screen_manager.current = "programs_screen"
        programs_screen = self.root.ids.screen_manager.get_screen('programs_screen')
        programs_screen.on_enter()
        nav_bar = self.root.ids.nav_bar
        prog_item = next((widget for widget in nav_bar.children if hasattr(widget, 'name') and widget.name == 'programs_screen'), None)
        if prog_item:
            nav_bar.set_active_item(prog_item)

            
if __name__ == '__main__':
    MainApp().run()