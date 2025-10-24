# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any, Dict, List, Optional
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy_garden.graph import Graph, LinePlot
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen

def _logic():
    return MDApp.get_running_app().logic

class GraphScreen(MDScreen):
    selected_program_id = NumericProperty(None, allownone=True)
    selected_exercise_id = NumericProperty(None, allownone=True)

    program_button_text = StringProperty("Программа")
    exercise_button_text = StringProperty("Упражнение")

    _chart_data = ObjectProperty(None, allownone=True)
    _graph = ObjectProperty(None, allownone=True)

    program_menu = ObjectProperty(None, allownone=True)
    exercise_menu = ObjectProperty(None, allownone=True)

    def on_enter(self, *args):
        self.reset_view()
        self.setup_program_dropdown()

    def reset_view(self):
        self.program_button_text = "Программа"
        self.exercise_button_text = "Упражнение"
        self.selected_program_id = None
        self.selected_exercise_id = None
        self.ids.graph_container.clear_widgets()
        self.ids.selected_point_label.text = "Сначала выберите программу и упражнение"

        if self.program_menu:
            self.program_menu.dismiss()
        if self.exercise_menu:
            self.exercise_menu.dismiss()
        self.program_menu = None
        self.exercise_menu = None

    def setup_program_dropdown(self):
        logic = _logic()
        
        programs: List[Dict[str, Any]] = logic.list_programs() or []
        active_program = logic.get_active_program()

        if active_program:
            self.program_button_text = active_program.get("name", "Программа")
            self.selected_program_id = active_program.get("id")
        
        if not programs:
            self.ids.selected_point_label.text = "Сначала создайте программу тренировок"

        menu_items = [
            {
                "text": p.get("name", "Без имени"),
                "on_release": lambda p=p: self.select_program(p),
            }
            for p in programs
        ]

        self.program_menu = MDDropdownMenu(
            caller=self.ids.program_dropdown_button,
            items=menu_items,
            width_mult=4,
        )

        if self.selected_program_id is not None:
            program = logic.get_program_by_id(int(self.selected_program_id))
            self._build_exercise_menu_for_program(program)

    def _build_exercise_menu_for_program(self, program_data: Optional[Dict[str, Any]]):
        if self.exercise_menu:
            self.exercise_menu.dismiss()
        
        self.exercise_button_text = "Упражнение"
        self.selected_exercise_id = None
        self.ids.graph_container.clear_widgets()
        
        menu_items = []
        if program_data:
            exercises = program_data.get("exercises", [])
            menu_items = [
                {
                    "text": ex.get("name", "Без имени"),
                    "on_release": lambda ex=ex: self.select_exercise(ex),
                }
                for ex in exercises
            ]
            self.ids.selected_point_label.text = "Теперь выберите упражнение"
        
        self.exercise_menu = MDDropdownMenu(
            caller=self.ids.exercise_dropdown_button,
            items=menu_items,
            width_mult=4,
        )

    def select_program(self, program_data: Dict[str, Any]):
        self.program_button_text = program_data.get("name", "Программа")
        self.selected_program_id = program_data.get("id")
        self.program_menu.dismiss()
        self._build_exercise_menu_for_program(program_data)

    def select_exercise(self, exercise_data: Dict[str, Any]):
        self.exercise_button_text = exercise_data.get("name", "Упражнение")
        self.selected_exercise_id = exercise_data.get("id")
        self.exercise_menu.dismiss()
        self.ids.selected_point_label.text = ""
        self.render_graph()

    def render_graph(self):
        if self.selected_exercise_id is None:
            return

        logic = _logic()
        app = MDApp.get_running_app()
        self.ids.graph_container.clear_widgets()

        self._chart_data = logic.get_progress_chart_data(int(self.selected_exercise_id))

        if not self._chart_data or not self._chart_data.get("data"):
            self.ids.selected_point_label.text = "Вы еще не делали это упражнение"
            return

        one_rep_maxes = self._chart_data.get("data", [])
        final_points = list(enumerate(one_rep_maxes))
        plot_color = app.theme_cls.primaryColor
        ymax = max(one_rep_maxes) if one_rep_maxes else 10

        self._graph = Graph(
            ylabel="1ПМ (кг)",
            x_ticks_major=max(1, len(final_points) // 5),
            y_ticks_major=max(5, round(ymax / 5 if ymax else 5)),
            y_grid_label=True,
            x_grid_label=False,
            padding=dp(10),
            x_grid=True,
            y_grid=True,
            xmin=-0.5,
            xmax=len(final_points) - 0.5,
            ymin=0,
            ymax=ymax * 1.2 if ymax else 10,
            background_color=(0, 0, 0, 0),
            border_color=(0.3, 0.3, 0.3, 1),
            label_options={"color": app.theme_cls.primaryColor, "bold": True},
        )

        plot = LinePlot(color=plot_color, line_width=dp(2.5))
        plot.points = final_points
        self._graph.add_plot(plot)
        self.ids.graph_container.add_widget(self._graph)
        self.animate_plot(plot, final_points)

    def animate_plot(self, plot: LinePlot, final_points: List):
        if not self._graph:
            return
        plot.points = [(p[0], self._graph.ymin) for p in final_points]
        Animation(points=final_points, d=1.0, t="out_quad").start(plot)

