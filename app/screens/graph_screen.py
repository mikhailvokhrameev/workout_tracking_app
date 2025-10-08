from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Mesh
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.label import Label
from kivy_garden.graph import Graph, MeshLinePlot, LinePlot
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivy.metrics import dp

class GraphScreen(MDScreen):
    selected_program_id = NumericProperty(None, allownone=True)
    selected_exercise_id = NumericProperty(None, allownone=True)
    program_button_text = StringProperty("Программа")
    exercise_button_text = StringProperty("Упражнение")
    
    _chart_data = ObjectProperty(None, allownone=True)
    _graph = ObjectProperty(None, allownone=True)
    program_menu = ObjectProperty(None)
    exercise_menu = ObjectProperty(None)

    def on_pre_enter(self):
        if not self.program_menu:
            self.setup_program_dropdown()

    def setup_program_dropdown(self):
        app = MDApp.get_running_app()
        programs = app.logic.app_data.get('programs', [])
        menu_items = [{"text": p['name'], "on_release": lambda p=p: self.select_program(p)} for p in programs]
        self.program_menu = MDDropdownMenu(
            caller=self.ids.program_dropdown_button, items=menu_items, width_mult=4)

    def select_program(self, program_data):
        self.program_button_text = program_data['name']
        self.selected_program_id = program_data['id']
        self.program_menu.dismiss()
        
        self.exercise_button_text = "Select Exercise"
        self.selected_exercise_id = None
        self.ids.graph_container.clear_widgets()
        self.ids.selected_point_label.text = ""
        
        exercises = program_data.get('exercises', [])
        menu_items = [{"text": ex['name'], "on_release": lambda ex=ex: self.select_exercise(ex)} for ex in exercises]
        self.exercise_menu = MDDropdownMenu(
            caller=self.ids.exercise_dropdown_button, items=menu_items, width_mult=4)

    def select_exercise(self, exercise_data):
        self.exercise_button_text = exercise_data['name']
        self.selected_exercise_id = exercise_data['id']
        self.exercise_menu.dismiss()
        print(f"{self.selected_exercise_id} is selected")
        self.ids.selected_point_label.text = ""
        self.render_graph()

    def render_graph(self):
        if not self.selected_exercise_id:
            return

        app = MDApp.get_running_app()
        self.chart_data = app.logic.get_progress_chart_data(self.selected_exercise_id)
        
        self.ids.graph_container.clear_widgets()

        if not self.chart_data or not self.chart_data.get('data'):
            self.ids.selected_point_label.text = "Вы еще не делали это упражнение"
            return

        points = list(enumerate(self.chart_data['data']))
        one_rep_maxes = self.chart_data['data']
        plot_color = app.theme_cls.primaryColor

        self._graph = Graph(
            ylabel='1ПМ (кг)',
            x_ticks_major=max(1, len(points) // 4),
            y_ticks_major=max(5, round(max(one_rep_maxes) / 5 if one_rep_maxes else 5)),
            y_grid_label=True, x_grid_label=False, padding=dp(10),
            x_grid=True, y_grid=True, xmin=-0.5, xmax=len(points) - 0.5,
            ymin=0, ymax=max(one_rep_maxes) * 1.2 if one_rep_maxes else 10,
            background_color=(0, 0, 0, 0), border_color=(0.3, 0.3, 0.3, 1),
            label_options={'color': app.theme_cls.primaryColor, 'bold': True}
        )
        
        self.ids.selected_point_label.text = ""
        
        plot = LinePlot(color=plot_color, line_width=dp(2.5)) 
        
        self._graph.add_plot(plot)
        
        self.ids.graph_container.add_widget(self._graph)
        
        self.animate_plot(plot, points)

    def animate_plot(self, plot, final_points):
        plot.points = [(p[0], self._graph.ymin) for p in final_points]
        Animation(points=final_points, d=1.0, t='out_quad').start(plot)
