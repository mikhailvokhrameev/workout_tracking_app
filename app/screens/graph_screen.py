from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Mesh
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.label import Label
from kivy_garden.graph import Graph, MeshLinePlot
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
            y_grid_label=True, x_grid_label=False, padding=dp(15),
            x_grid=True, y_grid=True, xmin=-0.5, xmax=len(points) - 0.5,
            ymin=0, ymax=max(one_rep_maxes) * 1.2 if one_rep_maxes else 10,
            background_color=(0,0,0,0), border_color=(0.3, 0.3, 0.3, 1),
            label_options={'color': (0.8, 0.8, 0.8, 1), 'bold': True}
        )
        
        self.ids.selected_point_label.text = ""
        
        plot = MeshLinePlot(color=plot_color)
        plot.line_width = dp(2)
        
        self._graph.add_plot(plot)
        self.add_custom_x_labels()
        self.add_gradient_fill(points, plot_color)
        
        self.ids.graph_container.add_widget(self._graph)
        
        self.animate_plot(plot, points)
        self._graph.bind(on_touch_down=self.on_graph_touch)

    def add_custom_x_labels(self):
        dates = self.chart_data['labels']
        for i, date in enumerate(dates):
            if i % max(1, len(dates) // 4) == 0:
                label = Label(text=date, font_size='10sp', color=(0.8, 0.8, 0.8, 1))
                self._graph.add_widget(label)
                def update_pos(*_, index=i, lbl=label):
                    if self._graph and self._graph.parent:
                        pos_x, _ = self._graph.to_widget(index, 0)
                        lbl.pos = (pos_x - lbl.width / 2, self._graph.y + dp(2))
                self._graph.bind(pos=update_pos, size=update_pos)
                Clock.schedule_once(update_pos)
    
    def add_gradient_fill(self, points, color):
        if len(points) < 2: return
        with self._graph.canvas.before:
            Color(*color[:3], 0.3)
            self._gradient_mesh = Mesh(vertices=[], indices=[], mode='triangle_fan')
        def update_mesh(*_):
            v = [points[0][0], self._graph.ymin, 0, 0]
            v.extend(x for p in points for x in (p[0], p[1], 0, 0))
            v.extend([points[-1][0], self._graph.ymin, 0, 0])
            self._gradient_mesh.vertices = v
            self._gradient_mesh.indices = range(len(points) + 2)
        Clock.schedule_once(update_mesh)

    def animate_plot(self, plot, final_points):
        plot.points = [(p[0], self._graph.ymin) for p in final_points]
        Animation(points=final_points, d=1.0, t='out_quad').start(plot)

    def on_graph_touch(self, instance, touch):
        if self._graph and self._graph.collide_point(*touch.pos):
            for i, p in enumerate(self._graph.plots[0].points):
                wx, wy = self._graph.to_widget(p[0], p[1])
                if abs(touch.x - wx) < dp(20) and abs(touch.y - wy) < dp(20):
                    date = self.chart_data['labels'][i]
                    self.ids.selected_point_label.text = f"Date: {date}, 1RM: {p[1]:.2f} kg"
                    return True
        return False
