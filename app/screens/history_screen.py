# from kivymd.app import MDApp
# from kivymd.uix.screen import MDScreen
# from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemSupportingText, MDListItemTertiaryText
# from kivymd.uix.card import MDCard
# from kivy.properties import ObjectProperty
# from kivy.clock import Clock

# class HistorySessionCard(MDCard):
#     session = ObjectProperty(None)
#     screen = ObjectProperty(None)

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         Clock.schedule_once(self.populate_content)

#     def populate_content(self, *args):
#         container = self.ids.history_items_container
#         container.clear_widgets()
#         app = MDApp.get_running_app()
        
#         for ex_session in self.session.get('exercises', []):
#             exercise_id = ex_session.get('exerciseId')
            
#             if not exercise_id:
#                 continue

#             sets_string = ", ".join([f"{s['reps']}x{s['weight']}kg" for s in ex_session.get('sets', [])])
            
#             item = MDListItem(
#                 MDListItemSupportingText(
#                     text=ex_session.get('exerciseName', 'Unknown'),
#                 ),
#                 MDListItemTertiaryText(
#                     text=sets_string
#                 )
#             )
#             container.add_widget(item)
            

# class HistoryScreen(MDScreen):    
#     def on_enter(self, *args):
#         self.render_workout_history()

#     def render_workout_history(self):
#         app = MDApp.get_running_app()
#         container = self.ids.full_history_container
#         container.clear_widgets()
#         history = app.logic.app_data.get('workoutHistory', [])
        
#         for session in sorted(history, key=lambda x: x.get('date', ''), reverse=True):
#             card = HistorySessionCard(session=session, screen=self)
#             container.add_widget(card)
    
#     def delete_history_session(self, session_id):
#         app = MDApp.get_running_app()
#         if session_id:
#             app.logic.delete_history_session(session_id)
#             self.render_workout_history()

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemSupportingText, MDListItemTertiaryText
from kivymd.uix.card import MDCard
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from app.logic.components import SettingsTopAppBar

class HistorySessionCard(MDCard):
    session = ObjectProperty(None)
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.populate_content)

    def populate_content(self, *args):
        container = self.ids.history_items_container
        container.clear_widgets()
        app = MDApp.get_running_app()
        
        for ex_session in self.session.get('exercises', []):
            exercise_id = ex_session.get('exerciseId')
            
            if not exercise_id:
                continue

            sets_string = ", ".join([f"{s['reps']}x{s['weight']}kg" for s in ex_session.get('sets', [])])
            
            item = MDListItem(
                MDListItemSupportingText(
                    text=ex_session.get('exerciseName', 'Unknown'),
                ),
                MDListItemTertiaryText(
                    text=sets_string
                )
            )
            container.add_widget(item)
            

class HistoryScreen(MDScreen):    
    def on_enter(self, *args):
        self.render_workout_history()

    def render_workout_history(self):
        app = MDApp.get_running_app()
        container = self.ids.full_history_container
        container.clear_widgets()
        history = app.logic.app_data.get('workoutHistory', [])
        
        for session in sorted(history, key=lambda x: x.get('date', ''), reverse=True):
            card = HistorySessionCard(session=session, screen=self)
            container.add_widget(card)
    
    def delete_history_session(self, session_id):
        app = MDApp.get_running_app()
        if session_id:
            app.logic.delete_history_session(session_id)
            self.render_workout_history()