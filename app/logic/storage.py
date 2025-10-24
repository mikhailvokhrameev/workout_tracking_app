# -*- coding: utf-8 -*-

from __future__ import annotations
import json
from typing import Any, Dict, Optional


class AppStorage:
    def __init__(self, data_file: str = "app_data.json") -> None:
        self.data_file = data_file
        self.app_data: Dict[str, Any] = {
            "programs": [],
            "workoutHistory": [],
            "userSetupComplete": False,
            "activeProgramId": None,
        }

    def load(self) -> None:
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            self.app_data.update(saved_data)
            if "workoutHistory" not in self.app_data:
                self.app_data["workoutHistory"] = []
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.app_data, f, indent=4, ensure_ascii=False)
        except IOError:
            pass

    def get(self) -> Dict[str, Any]:
        return self.app_data

    def set(self, new_data: Dict[str, Any]) -> None:
        self.app_data = new_data
