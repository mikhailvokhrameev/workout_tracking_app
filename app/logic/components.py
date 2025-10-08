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

class ProgramsPlaceholder(MDBoxLayout):
    screen = ObjectProperty(None)

# class SettingsTopAppBar(MDBoxLayout):
#     # title = StringProperty("Заголовок")
#     # show_back_button = BooleanProperty(True)
#     _menu = None
#     _dialog = None

#     def open_settings_menu(self, caller):
#         if self._menu is None:
#             self._menu = MDDropdownMenu(
#                 caller=caller,
#                 items=[
#                     {
#                         "text": "Удалить все данные",
#                         "on_release": self._on_reset_all_data_pressed,
#                     }
#                 ],
#                 width_mult=4,
#                 position="auto",
#             )
#         self._menu.open()

#     def _on_reset_all_data_pressed(self, *args):
#         self._menu.dismiss()
#         self.open_confirm_dialog()

#     # def go_back(self, *args):
#     #     app = MDApp.get_running_app()
#     #     if hasattr(app.root, "current"):
#     #         app.root.current = "main_screen"

#     def open_confirm_dialog(self, *args):
#         if self._dialog is None:
#             self._dialog = MDDialog(
#                 MDDialogHeadlineText(text="Подтвердить удаление"),
#                 MDDialogSupportingText(text="Вы уверены, что хотите безвозвратно удалить все данные?\n\nЭто действие нельзя отменить"),        
#                 MDDialogButtonContainer(
#                             Widget(),
#                             MDButton(
#                                 MDButtonText(text="Отмена"),
#                                 style="text",
#                                 on_release=lambda x: self._dialog.dismiss(),
#                             ),
#                             MDButton(
#                                 MDButtonText(text="Удалить"),
#                                 style="text",
#                                 on_release=self._do_reset_all_data,
#                             ),
#                             Widget(),
#                             spacing="4dp",
#                         ),
#                     )
#             self._dialog.open()

#     def _do_reset_all_data(self, *args):
#         self._dialog.dismiss()
#         app = MDApp.get_running_app()
#         if hasattr(app, "execute_reset_all_data"):
#             app.execute_reset_all_data()

class SettingsTopAppBar(MDBoxLayout):
    title = StringProperty("Заголовок")
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
        if self._dialog is None:
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
        if hasattr(app, "execute_reset_all_data"):
            app.execute_reset_all_data()
            print("бум чикабум")
            

