class TimerModel:
    def __init__(self):
        # Timer variables
        self.remaining_time = 0
        self.timer_active = False
        self.timer_paused = False
        self.pomodoro_count = 0
        self.current_mode = "Work"  # "Work" or "Break"
        self.work_time = "25"
        self.break_time = "5"
        self.mode_index = 0  # Default to Pomodoro mode

    def start_timer(self, mode, current_mode):
        if mode == "Custom":
            try:
                if current_mode == "Work":
                    minutes = int(self.work_time)
                else:
                    minutes = int(self.break_time)
            except ValueError:
                return None, "Invalid Time"
        elif mode == "Pomodoro (25/5)":
            minutes = 25 if current_mode == "Work" else 5
        elif mode == "Long Focus (50/10)":
            minutes = 50 if current_mode == "Work" else 10

        self.remaining_time = minutes * 60
        self.timer_active = True
        self.timer_paused = False

        return self.remaining_time, None

    def pause_timer(self):
        if not self.timer_active:
            return False

        self.timer_paused = not self.timer_paused
        return self.timer_paused

    def skip_timer(self):
        if not self.timer_active:
            return False

        self.timer_active = False
        self.timer_paused = False

        # Toggle mode
        self.toggle_mode()
        return True

    def toggle_mode(self):
        self.current_mode = "Break" if self.current_mode == "Work" else "Work"
        return self.current_mode

    def update_countdown(self):
        if self.remaining_time <= 0:
            return True  # Timer complete

        self.remaining_time -= 1
        return False

    def get_next_timer_duration(self, mode):
        if mode == "Custom":
            try:
                if self.current_mode == "Work":
                    minutes = int(self.work_time)
                else:
                    minutes = int(self.break_time)
            except ValueError:
                minutes = 25 if self.current_mode == "Work" else 5
        elif mode == "Pomodoro (25/5)":
            minutes = 25 if self.current_mode == "Work" else 5
        elif mode == "Long Focus (50/10)":
            minutes = 50 if self.current_mode == "Work" else 10

        return minutes * 60

    def get_settings_dict(self):
        return {
            "pomodoro_count": self.pomodoro_count,
            "work_time": self.work_time,
            "break_time": self.break_time,
            "mode_index": self.mode_index,
        }

    def load_from_settings(self, settings):
        self.pomodoro_count = settings.get("pomodoro_count", 0)
        self.work_time = settings.get("work_time", "25")
        self.break_time = settings.get("break_time", "5")
        self.mode_index = settings.get("mode_index", 0)
