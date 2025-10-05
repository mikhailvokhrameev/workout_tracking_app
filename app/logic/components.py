from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

class BaseMDNavigationItem(MDNavigationItem):
    icon = StringProperty()
    text = StringProperty()

class ProgramsPlaceholder(MDBoxLayout):
    screen = ObjectProperty(None)