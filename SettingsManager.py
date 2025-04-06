import json


class SettingsManager:
    @staticmethod
    def save_settings(timer_model, task_manager, stats_manager, ai_assistant):
        settings = {}
        settings.update(timer_model.get_settings_dict())
        settings.update(task_manager.get_settings_dict())
        settings.update(stats_manager.get_settings_dict())
        settings.update(ai_assistant.get_settings_dict())

        try:
            with open("ai_timer_settings.json", "w") as f:
                json.dump(settings, f)
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False

    @staticmethod
    def load_settings():
        try:
            with open("ai_timer_settings.json", "r") as f:
                settings = json.load(f)
            return settings
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            return {}
