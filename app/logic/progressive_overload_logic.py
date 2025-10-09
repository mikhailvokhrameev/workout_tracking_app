import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

class ProgressiveOverloadLogic:
    def __init__(self, data_file='app_data.json'):
        self.data_file = data_file

        self.app_data: Dict[str, Any] = {
            'programs': [],
            'workoutHistory': [],
            'userSetupComplete': False,
            'activeProgramId': None
        }
        self.current_workout_state: Dict[int, List[Dict[str, Any]]] = {}
        
        self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                self.app_data.update(saved_data)
                if 'workoutHistory' not in self.app_data:
                    self.app_data['workoutHistory'] = []
                print("Data loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No saved data found or data is corrupt. Starting fresh.")
            pass
            
        if self.app_data['userSetupComplete']:
            if self.app_data['programs'] and not self.app_data['activeProgramId']:
                self.app_data['activeProgramId'] = self.app_data['programs'][0]['id']
            self.init_current_workout()

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.app_data, f, indent=4, ensure_ascii=False)
            print("Data saved successfully.")
        except IOError as e:
            print(f"Error saving data: {e}")

    def create_new_program(self, name: str, progression_type: str):
        new_program = {
            'id': int(time.time() * 1000),
            'name': name,
            'progressionType': progression_type,
            'exercises': []
        }
        self.app_data['programs'].append(new_program)
        self.app_data['activeProgramId'] = new_program['id']
        self.save_data()
        self.init_current_workout()

    def delete_program(self, program_id: int) -> bool:
        if len(self.app_data['programs']) <= 1:
            print("Cannot delete the last program.")
            return False
            
        self.app_data['programs'] = [p for p in self.app_data['programs'] if p['id'] != program_id]
        if self.app_data['activeProgramId'] == program_id:
            self.app_data['activeProgramId'] = self.app_data['programs'][0]['id'] if self.app_data['programs'] else None
        
        self.save_data()
        self.init_current_workout()
        return True

    def select_program(self, program_id: int):
        self.app_data['activeProgramId'] = program_id
        self.init_current_workout()
        self.save_data()

    def add_exercise_to_program(self, name: str):
        active_program = self.get_active_program()
        if active_program:
            new_exercise = {
                'id': int(time.time() * 1000),
                'name': name,
                'history': [],
                'nextTarget': None
            }
            active_program['exercises'].append(new_exercise)
            if new_exercise['id'] not in self.current_workout_state:
                self.current_workout_state[new_exercise['id']] = []
            self.save_data()

    def delete_exercise(self, exercise_id: int):
        active_program = self.get_active_program()
        if active_program:
            active_program['exercises'] = [ex for ex in active_program['exercises'] if ex['id'] != exercise_id]
            if exercise_id in self.current_workout_state:
                del self.current_workout_state[exercise_id]
            self.save_data()
    
    def init_current_workout(self):
        self.current_workout_state = {}
        active_program = self.get_active_program()
        if active_program:
            for ex in active_program['exercises']:
                self.current_workout_state[ex['id']] = []
    
    
    def add_set_to_workout(self, exercise_id: int):
        if exercise_id not in self.current_workout_state:
            self.current_workout_state[exercise_id] = []

        self.current_workout_state[exercise_id].append({
            'id': int(time.time() * 1000),
            'type': 'normal',
            'weight': '',
            'reps': ''
        })

    def delete_set_from_workout(self, exercise_id: int, set_id: int):
        self.current_workout_state[exercise_id] = [
            s for s in self.current_workout_state[exercise_id] if s['id'] != set_id
        ]
        
    def update_set_in_workout(self, exercise_id: int, set_id: int, property_name: str, value: str):
        for s in self.current_workout_state[exercise_id]:
            if s['id'] == set_id:
                s[property_name] = value
                break

    def save_workout(self) -> Optional[Dict[str, Any]]:
        active_program = self.get_active_program()
        if not active_program:
            return None

        workout_session = {
            'id': int(time.time() * 1000),
            'date': datetime.now().strftime('%d.%m.%Y'),
            'programId': active_program['id'],
            'programName': active_program['name'],
            'exercises': []
        }
        
        saved_exercises_data_for_summary = []

        for exercise_id_str, sets in self.current_workout_state.items():
            exercise_id = int(exercise_id_str)
            exercise = self.find_exercise_by_id(exercise_id)
            
            sets_to_save = []
            for s in sets:
                if str(s.get('weight', '')).strip() and str(s.get('reps', '')).strip():
                    try:
                        sets_to_save.append({
                            **s,
                            'weight': float(s['weight']),
                            'reps': int(s['reps'])
                        })
                    except (ValueError, TypeError):
                        continue
            
            if exercise and sets_to_save:
                last_history = exercise['history'][-1] if exercise['history'] else None
                new_history_entry = {
                    'date': workout_session['date'],
                    'sets': sets_to_save
                }
                exercise['history'].append(new_history_entry)

                saved_exercises_data_for_summary.append({
                    'exercise': exercise,
                    'newSets': new_history_entry['sets'],
                    'lastHistory': last_history
                })

                workout_session['exercises'].append({
                    'exerciseId': exercise['id'],
                    'exerciseName': exercise['name'],
                    'sets': new_history_entry['sets']
                })
        
        if workout_session['exercises']:
            self.app_data['workoutHistory'].append(workout_session)
            summary_result = self.generate_workout_summary(saved_exercises_data_for_summary)
            self.save_data()
            self.init_current_workout()
            return summary_result
        else:
            print("No valid sets recorded to save.")
            return None

    def generate_workout_summary(self, saved_exercises_data: List[Dict]) -> Dict[str, Any]:
        all_goals_achieved = True
        summary_details = []

        for item in saved_exercises_data:
            exercise_data = item['exercise']
            new_sets = item['newSets']
            new_working_sets = [s for s in new_sets if s.get('type') == 'normal']
            if not new_working_sets:
                continue

            active_program = self.get_program_by_id(exercise_data['programId'])
            if not active_program:
                active_program = self.get_active_program()

            # --- ИЗМЕНЕНИЕ ЗДЕСЬ: НАХОДИМ ОРИГИНАЛЬНЫЙ ОБЪЕКТ УПРАЖНЕНИЯ ---
            program_exercise = next((ex for ex in active_program['exercises'] if ex['id'] == exercise_data['id']), None)
            if not program_exercise:
                continue

            progression_type = active_program.get('progressionType', 'double')
            has_previous_target = program_exercise.get('nextTarget') is not None
            
            detail = {'exercise_name': program_exercise['name']}

            if not has_previous_target:
                detail['status'] = 'success'
                detail['message'] = "Отличное начало! "
                # --- ИЗМЕНЕНИЕ ЗДЕСЬ: ОБНОВЛЯЕМ ОРИГИНАЛ ---
                program_exercise['nextTarget'] = self._calculate_next_target(program_exercise, {'sets': new_working_sets}, progression_type)
                detail['next_target_text'] = (
                    f"Цель на следующую тренировку: {program_exercise['nextTarget']['text']}"
                    f"{f' с весом {program_exercise['nextTarget']['weight']} кг' if 'weight' in program_exercise['nextTarget'] else ''}"
                )
            else:
                is_goal_achieved = self._check_goal_achievement(program_exercise, new_working_sets, progression_type)
                if is_goal_achieved:
                    detail['status'] = 'success'
                    detail['message'] = "Цель достигнута! "
                    # --- ИЗМЕНЕНИЕ ЗДЕСЬ: ОБНОВЛЯЕМ ОРИГИНАЛ ---
                    program_exercise['nextTarget'] = self._calculate_next_target(program_exercise, {'sets': new_working_sets}, progression_type)
                    detail['next_target_text'] = (
                        f"Следующая цель: {program_exercise['nextTarget']['text']}"
                        f"{f' с весом {program_exercise['nextTarget']['weight']} кг' if 'weight' in program_exercise['nextTarget'] else ''}"
                    )
                else:
                    all_goals_achieved = False
                    detail['status'] = 'failure'
                    detail['message'] = "Цель не достигнута. "
                    detail['next_target_text'] = (
                        f"Повторите: {program_exercise['nextTarget']['text']}"
                        f"{f' с весом {program_exercise['nextTarget']['weight']} кг' if 'weight' in program_exercise['nextTarget'] else ''}"
                    )
            summary_details.append(detail)
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ: СОХРАНЯЕМ ИЗМЕНЕНИЯ В ФАЙЛ ---
        self.save_data()
            
        return {
            "all_goals_achieved": all_goals_achieved,
            "details": summary_details
        }
    
    def _calculate_next_target(self, exercise: Dict, last_workout: Dict, progression_type: str) -> Dict:
        last_working_sets = [s for s in last_workout.get('sets', []) if s.get('type') == 'normal']

        if not last_working_sets:
            base_text = {
                'linear': "5 подходов по 5 повторений",
                'double': "3 подхода по 6-10 повторений",
                'rep_range': "3 подхода по 8-12 повторений"
            }
            return {
                'weight': 20,
                'sets': 5 if progression_type == 'linear' else 3,
                'reps': 5 if progression_type == 'linear' else ("8-12" if progression_type == 'rep_range' else 6),
                'text': base_text.get(progression_type, base_text['double'])
            }

        last_weight = float(last_working_sets[0]['weight'])
        weight_increment = 2.5 if last_weight > 40 else 1.25
        new_weight = round((last_weight + weight_increment) * 4) / 4

        targets = {
            'linear': {'weight': new_weight, 'sets': 5, 'reps': 5, 'text': "5 подходов по 5 повторений"},
            'double': {'weight': new_weight, 'sets': 3, 'reps': 6, 'text': "3 подхода по 6-10 повторений"},
            'rep_range': {'weight': new_weight, 'sets': 3, 'reps': "8-12", 'text': "3 подхода по 8-12 повторений"}
        }
        return targets.get(progression_type, targets['rep_range'])

    def _check_goal_achievement(self, exercise: Dict, new_working_sets: List[Dict], progression_type: str) -> bool:
        if not exercise.get('nextTarget'):
            return True

        try:
            target_weight = float(exercise['nextTarget']['weight'])
            
            if progression_type == 'linear':
                linear_sets = new_working_sets[:5]
                return (len(linear_sets) >= 5 and
                        all(s['reps'] >= 5 and s['weight'] >= target_weight for s in linear_sets))
            
            elif progression_type == 'double':
                double_sets = new_working_sets[:3]
                return (len(double_sets) >= 3 and
                        all(s['reps'] >= 10 and s['weight'] >= target_weight for s in double_sets))

            elif progression_type == 'rep_range':
                main_set = new_working_sets[0] if new_working_sets else None
                return (main_set and main_set['reps'] >= 12 and main_set['weight'] >= target_weight)
                
            return True
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error in _check_goal_achievement: {e}")
            return True

    def _calculate_one_rep_max(self, working_sets: List[Dict]) -> float:
        if not working_sets:
            return 0.0

        max_one_rep_max = 0.0
        for s in working_sets:
            weight = float(s['weight'])
            reps = int(s['reps'])
            if reps == 1:
                one_rep_max = weight
            elif reps > 1:
                # Формула Эпли: 1RM = w * (1 + r / 30)
                one_rep_max = weight * (1 + reps / 30)
            else:
                one_rep_max = 0.0

            if one_rep_max > max_one_rep_max:
                max_one_rep_max = one_rep_max
        
        return max_one_rep_max

    def delete_history_session(self, session_id: int):
        session_to_delete = next((s for s in self.app_data['workoutHistory'] if s['id'] == session_id), None)
        if not session_to_delete:
            return
        
        self.app_data['workoutHistory'] = [s for s in self.app_data['workoutHistory'] if s['id'] != session_id]

        for program in self.app_data['programs']:
            for exercise in program['exercises']:
                is_exercise_in_session = any(
                    ex['exerciseId'] == exercise['id'] for ex in session_to_delete.get('exercises', [])
                )
                if is_exercise_in_session:
                    exercise['history'] = [
                        h for h in exercise['history'] if h['date'] != session_to_delete['date']
                    ]
        
        self.save_data()

    def get_progress_chart_data(self, exercise_id: int) -> Optional[Dict[str, List]]:
        exercise = self.find_exercise_by_id(exercise_id)
        if not exercise or not exercise['history']:
            return None

        labels = [h['date'] for h in exercise['history']]
        one_rep_max_data = [
            self._calculate_one_rep_max([s for s in h['sets'] if s.get('type') == 'normal'])
            for h in exercise['history']
        ]

        return {'labels': labels, 'data': one_rep_max_data}
    
    def get_active_program(self) -> Optional[Dict[str, Any]]:
        if not self.app_data['activeProgramId']:
            return None
        return next((p for p in self.app_data['programs'] if p['id'] == self.app_data['activeProgramId']), None)

    def find_exercise_by_id(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        for p in self.app_data['programs']:
            for ex in p['exercises']:
                if ex['id'] == exercise_id:
                    return {**ex, 'programId': p['id']}
        return None
        
    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        return next((p for p in self.app_data['programs'] if p['id'] == program_id), None)

    def reset_all_data(self):
        self.app_data = {
            'programs': [],
            'workoutHistory': [],
            'userSetupComplete': False,
            'activeProgramId': None
        }
        self.current_workout_state = {}
        self.save_data()