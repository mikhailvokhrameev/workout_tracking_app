from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivy.uix.widget import Widget

class BaseMDNavigationItem(MDNavigationItem):
    icon = StringProperty()
    text = StringProperty()

class SettingsTopAppBar(MDBoxLayout):
    title = StringProperty("Заголовок")
    screen_manager = ObjectProperty(None)
    show_back_button = BooleanProperty(True)
    _menu = None
    _dialog = None

    def _reset_dialog(self, *args):
        self._dialog = None

    def open_settings_menu(self, caller):
        if self._menu is None:
            self._menu = MDDropdownMenu(
                caller=caller,
                items=[
                    {
                        "text": "Удалить все данные",
                        "on_release": self._on_reset_all_data_pressed,
                    }
                ],
                width_mult=4,
                position="auto",
            )
        self._menu.open()

    def _on_reset_all_data_pressed(self, *args):
        self._menu.dismiss()
        self.open_confirm_dialog()

    def go_back(self, *args):
        app = MDApp.get_running_app()
        if hasattr(app.root, "current"):
            app.root.current = "main_screen"

    def open_confirm_dialog(self, *args):
        # Всегда создаем новый диалог
        self._dialog = MDDialog(
            MDDialogHeadlineText(text="Подтвердить удаление"),
            MDDialogSupportingText(
                text="Вы уверены, что хотите безвозвратно "
                     "удалить все данные?\n\nЭто действие нельзя отменить."
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Отмена"),
                    style="text",
                    on_release=lambda x: self._dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Удалить"),
                    style="text",
                    on_release=self._do_reset_all_data,
                ),
                Widget(),
                spacing="2dp",
            ),
        )
        self._dialog.on_dismiss = self._reset_dialog
        self._dialog.open()

    def _do_reset_all_data(self, *args):
        self._dialog.dismiss()
        app = MDApp.get_running_app()
        if hasattr(app, "reset_all_data"):
            app.reset_all_data()
    
    def show_progression_info(self):
        """Переключает на экран с информацией о прогрессии"""
        if self.screen_manager.current == "progressive_overload_screen":
            self.go_back()
        else:
            self.last_screen = self.screen_manager.current
            self.screen_manager.transition.direction = 'right'
            self.screen_manager.current = "progressive_overload_screen"
        
    def go_back(self):
        if self.screen_manager and hasattr(self, 'last_screen'):
            self.screen_manager.transition.direction = 'left'
            self.screen_manager.current = self.last_screen
        elif self.screen_manager:
            self.screen_manager.current = 'program_screen'
        
