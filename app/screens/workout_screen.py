from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, StringProperty,  ListProperty, BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock
from kivymd.uix.expansionpanel import MDExpansionPanel
from kivymd.uix.behaviors import RotateBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.list import MDListItemTrailingIcon
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer
)
from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel


class WorkoutSummaryContent(MDBoxLayout):
    summary_text = StringProperty("")

# class NewSetRow(MDBoxLayout):
#     """Виджет для одного сета упражнения"""
#     exercise_id = ObjectProperty(None)
#     set_id = ObjectProperty(None)
#     weight = StringProperty('')
#     reps = StringProperty('')
#     panel_ref = ObjectProperty(None)
#     set_number = StringProperty('')
    
#     weight_error = BooleanProperty(False)
#     reps_error = BooleanProperty(False)
    
#     def on_weight(self, instance, value):
#         """Вызывается при изменении веса."""
#         is_valid = True
#         try:
#             if value: # Проверяем, только если поле не пустое
#                 val = float(value)
#                 if not (0 <= val < 1000):
#                     is_valid = False
#         except (ValueError, TypeError):
#             is_valid = False
        
#         self.weight_error = not is_valid

#     def on_reps(self, instance, value):
#         """Вызывается при изменении повторений."""
#         is_valid = True
#         try:
#             if value: # Проверяем, только если поле не пустое
#                 val = int(value)
#                 if not (0 <= val < 100):
#                     is_valid = False
#         except (ValueError, TypeError):
#             is_valid = False
            
#         self.reps_error = not is_valid
class NewSetRow(MDBoxLayout):
    """
    Виджет для одного сета упражнения с валидацией и сохранением состояния ошибки.
    """
    exercise_id = ObjectProperty(None)
    set_id = ObjectProperty(None)
    weight = StringProperty('')
    reps = StringProperty('')
    panel_ref = ObjectProperty(None)
    set_number = StringProperty('')
    
    # Свойства для управления состоянием ошибки в UI
    weight_error = BooleanProperty(False)
    reps_error = BooleanProperty(False)
    
    def on_weight(self, instance, value):
        """Вызывается при изменении свойства weight."""
        self._validate_and_update('weight', value)

    def on_reps(self, instance, value):
        """Вызывается при изменении свойства reps."""
        self._validate_and_update('reps', value)

    def _validate_and_update(self, property_name, value):
        """
        Общая функция для валидации, обновления UI (error property)
        и сохранения состояния ошибки в бизнес-логике.
        """
        is_valid = True
        try:
            # Пустое значение считается валидным, чтобы не показывать ошибку на пустых полях
            if not value:
                is_valid = True
            elif property_name == 'weight':
                val = float(value)
                if not (0 <= val < 1000):
                    is_valid = False
            elif property_name == 'reps':
                val = int(value)
                if not (0 <= val < 100):
                    is_valid = False
        except (ValueError, TypeError):
            is_valid = False

        # # 1. Обновляем UI, устанавливая флаг ошибки
        # if property_name == 'weight':
        #     self.weight_error = not is_valid
        # elif property_name == 'reps':
        #     self.reps_error = not is_valid
            
        # # 2. Сохраняем состояние ошибки в бизнес-логике (в current_workout_state)
        # logic = MDApp.get_running_app().logic
        # logic.update_set_error_state(self.exercise_id, self.set_id, property_name, not is_valid) 
        target_property = f"{property_name}_error"
        
        # 1. Сначала всегда сбрасываем ошибку
        setattr(self, target_property, False)
        
        # 2. Если ошибка есть, устанавливаем ее снова в следующем кадре
        if not is_valid:
            Clock.schedule_once(lambda dt: setattr(self, target_property, True), 0)
            
        # 3. Сохраняем состояние ошибки в бизнес-логике
        logic = MDApp.get_running_app().logic
        logic.update_set_error_state(self.exercise_id, self.set_id, property_name, not is_valid)

    
class TrailingPressedIconButton(
    ButtonBehavior, RotateBehavior, MDListItemTrailingIcon
):
    pass
    
class ExpansionPanelItem(MDExpansionPanel):
    exercise_id = ObjectProperty(None)
    exercise_name = StringProperty('')
    target_info = StringProperty('')
    last_workout_info = StringProperty('')

    def on_open(self, *args):
        self.add_set_row()
    

    def add_set_row(self, set_data=None):
        logic = MDApp.get_running_app().logic
        exercise_id = self.exercise_id

        current_sets_count = len(self.ids.new_sets_container.children)
        if current_sets_count >= 5:
            print("Достигнуто ограничение в 5 подходов")
            return
        
        set_number = str(current_sets_count + 1)
        
        if set_data:
            set_id = set_data['id']
            weight = str(set_data['weight'])
            reps = str(set_data['reps'])
        else:
            logic.add_set_to_workout(exercise_id)
            new_set = logic.current_workout_state[exercise_id][-1]
            set_id = new_set['id']
            weight, reps = '', ''

        set_row = NewSetRow(
            exercise_id=exercise_id,
            set_id=set_id,
            weight=weight,
            reps=reps,
            panel_ref=self
        )
        self.ids.new_sets_container.add_widget(set_row)
        

    def remove_set_row(self, set_row):
        logic = MDApp.get_running_app().logic
        logic.delete_set_from_workout(set_row.exercise_id, set_row.set_id)
        self.ids.new_sets_container.remove_widget(set_row)


class WorkoutScreen(MDScreen):
    dialog = None
    pending_workout_data = None
    
    def on_enter(self, *args):
        Clock.schedule_once(self.render_todays_workout)

    def render_todays_workout(self, *args):
        logic = MDApp.get_running_app().logic
        container = self.ids.today_workout_container
        container.clear_widgets()

        active_program = logic.get_active_program()
        
        if not active_program:
            # Отображаем заглушку или сообщение о необходимости создать программу
            placeholder = MDLabel(
                text= "Нет активной программы",
                halign="center",
                theme_text_color="Secondary"
            )
            container.add_widget(placeholder)
            return
        
        for ex in active_program['exercises']:
            last_workout = ex['history'][-1] if ex['history'] else None
            last_workout_text = "Это первая тренировка!"
            if last_workout:
                sets_str = ", ".join([f"{s['reps']}x{s['weight']}кг" for s in last_workout['sets']])
                last_workout_text = f"Прошлая: {sets_str}"

            target_text = "Выполните рабочие подходы"
            if ex.get('nextTarget'):
                target = ex['nextTarget']
                target_text = f"Цель: {target['text']} с весом ~[b]{target['weight']} кг[/b]"

            panel = ExpansionPanelItem(
                exercise_id=ex['id'],
                exercise_name=ex['name'],
                target_info=target_text,
                last_workout_info=last_workout_text
            )

            for s in logic.current_workout_state.get(ex['id'], []):
                panel.add_set_row(set_data=s)

            container.add_widget(panel)
    
    def _collect_ui_data(self):
        logic = MDApp.get_running_app().logic
        for panel in reversed(self.ids.today_workout_container.children):
            if isinstance(panel, ExpansionPanelItem):
                for set_row in panel.ids.new_sets_container.children:
                    logic.update_set_in_workout(
                        set_row.exercise_id, set_row.set_id,
                        'weight', set_row.ids.weight_input.text
                    )
                    logic.update_set_in_workout(
                        set_row.exercise_id, set_row.set_id,
                        'reps', set_row.ids.reps_input.text
                    )

    # def show_save_confirmation_dialog(self):
    #     app = MDApp.get_running_app()
    #     logic = MDApp.get_running_app().logic
    #     self._collect_ui_data()
        
    #     if logic.has_validation_errors():
    #         print("Нельзя сохранить тренировку, есть ошибки в данных")
    #         # Здесь можно показать диалог с ошибкой или toast
    #         return

    #     active_program = app.logic.get_active_program()
    #     if not active_program:
    #         print("No active program found.")
    #         return

    #     saved_exercises_data = []
    #     for exercise in active_program['exercises']:
    #         exercise_id = exercise['id']
    #         workout_sets = app.logic.current_workout_state.get(exercise_id, [])
            
    #         sets_to_save = []
    #         for s in workout_sets:
    #             if str(s.get('weight', '')).strip() and str(s.get('reps', '')).strip():
    #                 try:
    #                     sets_to_save.append({**s, 'weight': float(s['weight']), 'reps': int(s['reps'])})
    #                 except (ValueError, TypeError):
    #                     continue
            
    #         if sets_to_save:
    #             last_history = exercise['history'][-1] if exercise['history'] else None
    #             exercise_with_program = {**exercise, 'programId': active_program['id']}
    #             saved_exercises_data.append({
    #                 'exercise': exercise_with_program,
    #                 'newSets': sets_to_save,
    #                 'lastHistory': last_history
    #             })
        
    #     if not saved_exercises_data:
    #         print("No valid sets recorded to save.")
    #         return
        
    #     summary_data = app.logic.generate_workout_summary(saved_exercises_data)
    #     final_text = ""
    #     if not summary_data['all_goals_achieved']:
    #         final_text += "Ничего страшного!\n"
    #         final_text += "Результаты оказались чуть ниже. Это нормально. Главное — не сдаваться!\n\n"
    #     final_text += "[b]Детали прогресса:[/b]\n\n"
    #     for detail in summary_data['details']:
    #         final_text += f"{detail['exercise_name']}: {detail['message']}\n"
    #         final_text += f"{detail['next_target_text']}\n\n"

    #     if self.dialog:
    #         self.dialog.dismiss()
    #         self.dialog = None

    #     self.dialog = MDDialog(
    #         MDDialogHeadlineText(text="Сохранить тренировку?", halign="center"),
    #         MDDialogContentContainer(
    #             WorkoutSummaryContent(summary_text=final_text),
    #             orientation='vertical'
    #         ),
    #         MDDialogButtonContainer(
    #             Widget(),
    #             MDButton(MDButtonText(text="Отмена"), style="text", on_release=self.close_dialog),
    #             MDButton(MDButtonText(text="Сохранить"), style="text", on_release=self.save_and_close_dialog),
    #             spacing="8dp",
    #         ),
    #         size_hint_x=0.9,
    #         auto_dismiss=False,
    #     )
    #     self.dialog.open()
    
    
    
    def show_save_confirmation_dialog(self):
        """
        Собирает данные, проверяет ошибки и показывает диалог с предпросмотром
        результатов тренировки. Не изменяет основные данные.
        """
        app = MDApp.get_running_app()
        logic = app.logic

        # 1. Проверка на ошибки валидации перед показом диалога
        if logic.has_validation_errors():
            # Здесь можно показать toast или простой диалог об ошибке
            print("Нельзя сохранить тренировку, есть ошибки в данных.")
            # Пример простого диалога с ошибкой:
            if not self.dialog:
                 self.dialog = MDDialog(
                     MDDialogHeadlineText(text="Ошибка"),
                     MDDialogSupportingText(text="Пожалуйста, исправьте некорректные значения веса или повторений"),
                     MDDialogButtonContainer(
                         MDButton(MDButtonText(text="OK"), style="text", on_release=self.close_dialog),
                         spacing="8dp",
                     ),
                 )
                 self.dialog.open()
            return

        # 2. Сбор актуальных данных из UI
        self._collect_ui_data()
        
        active_program = logic.get_active_program()
        if not active_program:
            print("Нет активной программы.")
            return

        # 3. Подготовка данных для предпросмотра и сохранения
        saved_exercises_data = []
        for exercise in active_program['exercises']:
            exercise_id = exercise['id']
            workout_sets = logic.current_workout_state.get(exercise_id, [])
            
            sets_to_save = []
            for s in workout_sets:
                if str(s.get('weight', '')).strip() and str(s.get('reps', '')).strip():
                    try:
                        sets_to_save.append({**s, 'weight': float(s['weight']), 'reps': int(s['reps'])})
                    except (ValueError, TypeError):
                        continue
            
            if sets_to_save:
                exercise['programId'] = active_program['id']
                
                saved_exercises_data.append({
                    'exercise': exercise,
                    'newSets': sets_to_save,
                })
        
        if not saved_exercises_data:
            print("Нет данных для сохранения.")
            return

        # 4. Сохраняем собранные данные во временное свойство
        self.pending_workout_data = saved_exercises_data
        
        # 5. Вызываем "read-only" функцию для генерации текста предпросмотра
        summary_data = logic.generate_workout_summary(self.pending_workout_data)
        
        final_text = ""
        if not summary_data['all_goals_achieved']:
            final_text += "Ничего страшного! Результаты оказались чуть ниже.\n\n"
        final_text += "[b]Детали прогресса:[/b]\n\n"
        for detail in summary_data['details']:
            final_text += f"{detail['exercise_name']}: {detail['message']}\n"
            final_text += f"{detail['next_target_text']}\n\n"
        
        # 6. Создаем и показываем диалог подтверждения
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Сохранить тренировку?"),
            MDDialogContentContainer(
                WorkoutSummaryContent(summary_text=final_text),
                orientation='vertical'
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(MDButtonText(text="Отмена"), style="text", on_release=self.close_dialog),
                MDButton(MDButtonText(text="Сохранить"), style="text", on_release=self.save_and_close_dialog),
                spacing="8dp",
            ),
            size_hint_x=0.9,
            auto_dismiss=False,
        )
        self.dialog.open()
    
    

    # def save_workout(self):
    #     logic = MDApp.get_running_app().logic
    #     app = MDApp.get_running_app()

    #     for panel in self.ids.today_workout_container.children:
    #         if isinstance(panel, ExpansionPanelItem):
    #             for set_row in panel.ids.new_sets_container.children:
    #                 logic.update_set_in_workout(
    #                     set_row.exercise_id,
    #                     set_row.set_id,
    #                     'weight',
    #                     set_row.ids.weight_input.text
    #                 )
    #                 logic.update_set_in_workout(
    #                     set_row.exercise_id,
    #                     set_row.set_id,
    #                     'reps',
    #                     set_row.ids.reps_input.text
    #                 )

    #     summary_result = logic.save_workout()
    #     if summary_result:
    #         app.switch_to_screen('history')
    
    def save_workout(self):
        """
        Вызывается для фактического сохранения тренировки.
        Собирает данные, передает их в `logic.save_workout` и переключает экран.
        """
        app = MDApp.get_running_app()
        logic = app.logic

        # 1. Обновляем current_workout_state последними данными из UI
        # Этот шаг важен, если пользователь не выходил из полей ввода
        self._collect_ui_data()

        # 2. Проверяем наличие ошибок валидации
        if logic.has_validation_errors():
            print("Сохранение отменено: есть ошибки валидации.")
            # Здесь можно показать диалог об ошибке
            return
            
        # 3. Готовим данные для сохранения (аналогично show_save_confirmation_dialog)
        active_program = logic.get_active_program()
        if not active_program:
            print("Нет активной программы для сохранения.")
            return

        saved_exercises_data = []
        for exercise in active_program['exercises']:
            workout_sets = logic.current_workout_state.get(exercise['id'], [])
            
            sets_to_save = []
            for s in workout_sets:
                if str(s.get('weight', '')).strip() and str(s.get('reps', '')).strip():
                    try:
                        sets_to_save.append({**s, 'weight': float(s['weight']), 'reps': int(s['reps'])})
                    except (ValueError, TypeError):
                        continue
            
            if sets_to_save:
                exercise_with_program_id = exercise.copy()
                exercise_with_program_id['programId'] = active_program['id']
                
                saved_exercises_data.append({
                    'exercise': exercise_with_program_id,
                    'newSets': sets_to_save,
                })

        if not saved_exercises_data:
            print("Нет сетов для сохранения.")
            return

        # 4. Вызываем метод сохранения из логики, ПЕРЕДАВАЯ ему подготовленные данные
        logic.save_workout(saved_exercises_data)
        
        # 5. Переключаем экран на историю
        app.switch_to_screen('history')
            
            

    # def close_dialog(self, *args):
    #     if self.dialog:
    #         self.dialog.dismiss()

    # def save_and_close_dialog(self, *args):
    #     app = MDApp.get_running_app()
    #     self.save_workout()
    #     self.close_dialog()
    
    
    def save_and_close_dialog(self, *args):
        """
        Вызывается при нажатии 'Сохранить' в диалоге.
        Выполняет фактическое сохранение и закрывает диалог.
        """
        if self.dialog:
            self.dialog.dismiss()
        
        if self.pending_workout_data:
            app = MDApp.get_running_app()
            # Вызываем метод, который реально изменяет и сохраняет данные
            app.logic.save_workout(self.pending_workout_data)
            self.pending_workout_data = None  # Очищаем временные данные
            
            # Опционально: переключаем экран после сохранения
            app.switch_to_screen('history')
        else:
            print("Нет данных для сохранения.")
            
    def close_dialog(self, *args):
        """Просто закрывает диалог."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None # Сбрасываем ссылку