from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
from kivymd.uix.card import MDCard

class HistorySessionCard(MDCard):
    session = ObjectProperty(None)
    screen = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.populate_content)
    
    def populate_content(self, *args):
        '''Вывод информации о тренировочной сессии'''
        container = self.ids.history_items_container
        container.clear_widgets()
        
        for ex in self.session.get('exercises', []):
            sets_string = ", ".join([f"{s['reps']}x{s['weight']}кг" for s in ex.get('sets', [])])
            item_text = f"[b]{ex.get('exerciseName', 'Unknown')}:[/b] {sets_string}"
            
            item = MDListItem(
                MDListItemHeadlineText(
                    text=ex.get('exerciseName', 'Unknown')
                ),
                MDListItemSupportingText(
                    text=sets_string
                )
            )
            container.add_widget(item)
        
        
    
class HistoryScreen(MDScreen):
    
    def on_enter(self, *args):
        '''обновляет список тренировочных сессий при каждом входе на экран'''
        self.render_workout_history()
        
    def render_workout_history(self):
        app = MDApp.get_running_app()
        container = self.ids.full_history_container
        container.clear_widgets()

        history = app.logic.app_data.get('workoutHistory', []) 

        if not history:
            self.ids.history_placeholder.opacity = 1
            self.ids.history_placeholder.height = self.height
            self.ids.history_placeholder.size_hint_y = 1
            self.ids.history_scroll_view.opacity = 0
        else:
            self.ids.history_placeholder.opacity = 0
            self.ids.history_placeholder.height = 0
            self.ids.history_placeholder.size_hint_y = None
            self.ids.history_scroll_view.opacity = 1
            
            for session in sorted(history, key=lambda x: x.get('date', ''), reverse=True):
                card = HistorySessionCard(session=session, screen=self)
                container.add_widget(card)

    def delete_history_session(self, session_id):
        '''Удаляет тренировочную сессию из истории'''
        app = MDApp.get_running_app()
        if session_id:
            app.logic.delete_history_session(session_id)
            self.render_workout_history()
    