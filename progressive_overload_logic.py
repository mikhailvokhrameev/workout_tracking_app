import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

class ProgressiveOverloadLogic:
    """
    Handles all the data management and business logic for the 
    Progressive Overload Assistant application
    """

    def __init__(self, data_file='app_data.json'):
        """
        Initializes the application state
        """
        self.data_file = data_file

        self.app_data: Dict[str, Any] = {
            'programs': [],
            'workoutHistory': [],
            'userSetupComplete': False,
            'activeProgramId': None
        }
        self.current_workout_state: Dict[int, List[Dict[str, Any]]] = {}
        
        self.load_data()

    # Initialization & Data Persistence

    def load_data(self):
        """
        Loads data from a local JSON file
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                # Basic validation and merging with default structure
                self.app_data.update(saved_data)
                if 'workoutHistory' not in self.app_data:
                    self.app_data['workoutHistory'] = []
                print("Data loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No saved data found or data is corrupt. Starting fresh.")
            # data is already initialized with defaults, so we just pass
            pass
            
        # post-load setup
        if self.app_data['userSetupComplete']:
            if self.app_data['programs'] and not self.app_data['activeProgramId']:
                self.app_data['activeProgramId'] = self.app_data['programs'][0]['id']
            self.init_current_workout()

    def save_data(self):
        """
        Saves the current application state to a JSON file
        """
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.app_data, f, indent=4, ensure_ascii=False)
            print("Data saved successfully.")
        except IOError as e:
            print(f"Error saving data: {e}")

    # Program & Exercise Management

    def create_new_program(self, name: str, progression_type: str):
        """
        The Kivy UI will provide the name and progression_type.
        Valid progression_type values: 'linear', 'double', 'rep_range'
        """
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
        """
        Returns False if the program cannot be deleted.
        """
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
        """
        Lets you select a training program
        """
        self.app_data['activeProgramId'] = program_id
        self.init_current_workout()
        self.save_data()

    def add_exercise_to_program(self, name: str):
        """
        Lets you add an exercise to your training program
        """
        active_program = self.get_active_program()
        if active_program:
            new_exercise = {
                'id': int(time.time() * 1000),
                'name': name,
                'history': [],
                'nextTarget': None
            }
            active_program['exercises'].append(new_exercise)
            # Ensure the exercise exists in the current workout state
            if new_exercise['id'] not in self.current_workout_state:
                self.current_workout_state[new_exercise['id']] = []
            self.save_data()

    def delete_exercise(self, exercise_id: int):
        """
        Lets you delete an exercise from your training program
        """
        active_program = self.get_active_program()
        if active_program:
            active_program['exercises'] = [ex for ex in active_program['exercises'] if ex['id'] != exercise_id]
            if exercise_id in self.current_workout_state:
                del self.current_workout_state[exercise_id]
            self.save_data()

    # Workout State & Logic

    def init_current_workout(self):
        """
        Lets you init current workout
        """
        self.current_workout_state = {}
        active_program = self.get_active_program()
        if active_program:
            for ex in active_program['exercises']:
                self.current_workout_state[ex['id']] = []
    
    
    def add_set_to_workout(self, exercise_id: int):
        """
        Called when 'add-set-btn' is clicked
        """
        # Safety Check
        if exercise_id not in self.current_workout_state:
            self.current_workout_state[exercise_id] = []

        self.current_workout_state[exercise_id].append({
            'id': int(time.time() * 1000),
            'type': 'normal',
            'weight': '',
            'reps': ''
        })

    def delete_set_from_workout(self, exercise_id: int, set_id: int):
        """
        Called when 'delete-set-btn' is clicked
        """
        self.current_workout_state[exercise_id] = [
            s for s in self.current_workout_state[exercise_id] if s['id'] != set_id
        ]
        
    def update_set_in_workout(self, exercise_id: int, set_id: int, property_name: str, value: str):
        """
        Updates set in a current workout
        """
        for s in self.current_workout_state[exercise_id]:
            if s['id'] == set_id:
                s[property_name] = value
                break

    def save_workout(self) -> Optional[Dict[str, Any]]:
        """
        Returns the summary generation data on success, otherwise None
        """
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
            
            # filter out empty sets and convert to correct types
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
                        continue # skip sets with invalid numbers
            
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

    # Progression Calculation & Feedback

    def generate_workout_summary(self, saved_exercises_data: List[Dict]) -> Dict[str, Any]:
        """
        Processes the completed workout and updates next targets.
        Returns a dictionary with summary details for the UI.
        """
        all_goals_achieved = True
        summary_details = []

        for item in saved_exercises_data:
            exercise = item['exercise']
            new_sets = item['newSets']
            new_working_sets = [s for s in new_sets if s.get('type') == 'normal']
            if not new_working_sets:
                continue

            active_program = self.get_program_by_id(exercise['programId']) # we need to find the program for the exercise
            if not active_program:
                active_program = self.get_active_program() # fallback
                
            progression_type = active_program.get('progressionType', 'double')

            has_previous_target = exercise.get('nextTarget') is not None
            
            detail = {'exercise_name': exercise['name']}

            if not has_previous_target:
                # first workout is always a success
                detail['status'] = 'success'
                detail['message'] = "Отличное начало! "
                exercise['nextTarget'] = self._calculate_next_target(exercise, {'sets': new_working_sets}, progression_type)
                detail['next_target_text'] = f"Цель на следующую тренировку: {exercise['nextTarget']['text']}"
            else:
                is_goal_achieved = self._check_goal_achievement(exercise, new_working_sets, progression_type)
                if is_goal_achieved:
                    detail['status'] = 'success'
                    detail['message'] = "Цель достигнута! "
                    exercise['nextTarget'] = self._calculate_next_target(exercise, {'sets': new_working_sets}, progression_type)
                    detail['next_target_text'] = f"Следующая цель: {exercise['nextTarget']['text']}"
                else:
                    all_goals_achieved = False
                    detail['status'] = 'failure'
                    detail['message'] = "Цель не достигнута. "
                    # the target is not changed
                    detail['next_target_text'] = f"Повторите: {exercise['nextTarget']['text']}"
            summary_details.append(detail)
            
        return {
            "all_goals_achieved": all_goals_achieved,
            "details": summary_details
        }

    
    def _calculate_next_target(self, exercise: Dict, last_workout: Dict, progression_type: str) -> Dict:
        """
        Internal helper method
        """
        # check for empty sets
        last_working_sets = [s for s in last_workout.get('sets', []) if s.get('type') == 'normal']

        # if no sets, it's the first time. Return a default starting target
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
        """
        Internal helper method
        """
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
                
            return True # default case
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error in _check_goal_achievement: {e}")
            return True # fail safe

    def _calculate_one_rep_max(self, working_sets: List[Dict]) -> float:
        """
        Internal helper method. Uses the Epley formula
        """
        if not working_sets:
            return 0.0

        max_one_rep_max = 0.0
        for s in working_sets:
            weight = float(s['weight'])
            reps = int(s['reps'])
            if reps == 1:
                one_rep_max = weight
            elif reps > 1:
                # Epley formula: 1RM = w * (1 + r / 30)
                one_rep_max = weight * (1 + reps / 30)
            else:
                one_rep_max = 0.0

            if one_rep_max > max_one_rep_max:
                max_one_rep_max = one_rep_max
        
        return max_one_rep_max

    # History Management

    def delete_history_session(self, session_id: int):
        """
        Deletes history session
        """
        session_to_delete = next((s for s in self.app_data['workoutHistory'] if s['id'] == session_id), None)
        if not session_to_delete:
            return

        # remove session from main history
        self.app_data['workoutHistory'] = [s for s in self.app_data['workoutHistory'] if s['id'] != session_id]

        # remove corresponding entries from each exercise's history
        for program in self.app_data['programs']:
            for exercise in program['exercises']:
                # find which exercises were in the deleted session
                is_exercise_in_session = any(
                    ex['exerciseId'] == exercise['id'] for ex in session_to_delete.get('exercises', [])
                )
                if is_exercise_in_session:
                    # filter out the history entry with the matching date
                    exercise['history'] = [
                        h for h in exercise['history'] if h['date'] != session_to_delete['date']
                    ]
        
        self.save_data()
        # full UI refresh would be required here

    # Progress Chart Data Preparation

    def get_progress_chart_data(self, exercise_id: int) -> Optional[Dict[str, List]]:
        """
        Prepares data for the progress chart.
        Returns a dictionary with 'labels' (dates) and 'data' (1RM values)
        """
        exercise = self.find_exercise_by_id(exercise_id)
        if not exercise or not exercise['history']:
            return None

        labels = [h['date'] for h in exercise['history']]
        one_rep_max_data = [
            self._calculate_one_rep_max([s for s in h['sets'] if s.get('type') == 'normal'])
            for h in exercise['history']
        ]

        return {'labels': labels, 'data': one_rep_max_data}

    # Utilities
    
    def get_active_program(self) -> Optional[Dict[str, Any]]:
        """
        Gets an active program
        """
        if not self.app_data['activeProgramId']:
            return None
        return next((p for p in self.app_data['programs'] if p['id'] == self.app_data['activeProgramId']), None)

    def find_exercise_by_id(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        """
        Adds the programId to the returned exercise dict for context, which is helpful
        """
        for p in self.app_data['programs']:
            for ex in p['exercises']:
                if ex['id'] == exercise_id:
                    # Return a copy with programId for context
                    return {**ex, 'programId': p['id']}
        return None
        
    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        """
        Helper to find a program by its ID
        """
        return next((p for p in self.app_data['programs'] if p['id'] == program_id), None)

    def reset_all_data(self):
        """
        Wipes the data file. The confirmation should be handled in the UI
        """
        self.app_data = {
            'programs': [],
            'workoutHistory': [],
            'userSetupComplete': False,
            'activeProgramId': None
        }
        self.current_workout_state = {}
        # this will effectively overwrite the file with a blank state
        self.save_data()