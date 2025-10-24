# -*- coding: utf-8 -*-

from __future__ import annotations
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window

from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.expansionpanel import MDExpansionPanel

from kivy.metrics import dp
from kivy.clock import Clock

from app.logic.logic import ProgressiveOverloadLogic
from app.logic.components import BaseMDNavigationItem, SettingsTopAppBar

from app.screens.programs_screen import ProgramsScreen, NewProgramDialog, ProgramCard
from app.screens.program_detail_screen import ProgramDetailScreen, ExerciseItem
from app.screens.main_screen import MainScreen
from app.screens.history_screen import HistoryScreen
from app.screens.workout_screen import (
    WorkoutScreen,
    NewSetRow,
    TrailingPressedIconButton,
    ExpansionPanelItem
)
from app.screens.graph_screen import GraphScreen
from app.screens.progressive_overload_screen import ProgressiveOverloadScreen

Window.keyboard_anim_args = {"d": .2, "t": "in_out_quart"}
Window.softinput_mode = "below_target"

class MainApp(MDApp):
    def build(self):
        self.logic = ProgressiveOverloadLogic(data_file="app_data.json")

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"

        return Builder.load_file("app/kv/main_screen.kv")

    def on_start(self):   
        self.root.ids.screen_manager.current = "programs_screen"

    def on_switch_tabs(
        self,
        bar: MDNavigationBar,
        item: MDNavigationItem,
        item_icon: str,
        item_text: str,
    ):
        self.root.ids.screen_manager.current = item.name

    def switch_to_screen(self, screen_name: str):
        target_screen_name = f"{screen_name}_screen"
        self.root.ids.screen_manager.current = target_screen_name

        nav_bar = self.root.ids.nav_bar
        item = next(
            (w for w in nav_bar.children if hasattr(w, "name") and w.name == target_screen_name),
            None,
        )
        if item:
            nav_bar.set_active_item(item)

    def tap_expansion_chevron(
        self,
        panel: MDExpansionPanel,
        chevron: TrailingPressedIconButton,
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
        programs_screen = self.root.ids.screen_manager.get_screen("programs_screen")
        
        if hasattr(programs_screen, "on_enter"):
            programs_screen.on_enter()

        nav_bar = self.root.ids.nav_bar
        prog_item = next((widget for widget in nav_bar.children if hasattr(widget, 'name') and widget.name == 'programs_screen'), None)
        if prog_item:
            nav_bar.set_active_item(prog_item)
            
            
if __name__ == '__main__':
    MainApp().run()