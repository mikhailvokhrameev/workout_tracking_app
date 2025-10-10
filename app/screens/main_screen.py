from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import ObjectProperty

class MainScreen(MDBoxLayout):
    app = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        