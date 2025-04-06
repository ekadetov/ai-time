class StatsManager:
    def __init__(self):
        self.daily_stats = {
            "focus_time": 0,
            "tasks_completed": 0,
            "pomodoros_completed": 0,
        }

    def update_work_completed(self, minutes):
        self.daily_stats["focus_time"] += minutes
        self.daily_stats["pomodoros_completed"] += 1

    def task_completed(self):
        self.daily_stats["tasks_completed"] += 1

    def get_stats_text(self, current_task="None"):
        stats_text = f"""
        Today's Productivity Stats:
        ---------------------------
        Focus time: {self.daily_stats['focus_time']} minutes
        Pomodoros completed: {self.daily_stats['pomodoros_completed']}
        Tasks completed: {self.daily_stats['tasks_completed']}
        
        Current task: {current_task if current_task else "None"}
        """

        return stats_text

    def get_settings_dict(self):
        return {"daily_stats": self.daily_stats}

    def load_from_settings(self, settings):
        self.daily_stats = settings.get(
            "daily_stats",
            {"focus_time": 0, "tasks_completed": 0, "pomodoros_completed": 0},
        )
