import json
import openai
import threading
from datetime import datetime


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


class TaskManager:
    def __init__(self):
        self.tasks = []
        self.current_task = ""

    def add_task(self, task):
        if not task:
            return False

        self.tasks.append(task)
        return True

    def complete_task(self, task):
        if not task or task not in self.tasks:
            return False

        self.tasks.remove(task)
        return True

    def get_task_list_text(self):
        if not self.tasks:
            return "No tasks added yet."

        task_text = ""
        for i, task in enumerate(self.tasks, 1):
            task_text += f"{i}. {task}\n"

        return task_text

    def get_settings_dict(self):
        return {"tasks": self.tasks}

    def load_from_settings(self, settings):
        self.tasks = settings.get("tasks", [])


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


class AIAssistant:
    def __init__(self):
        self.client = None
        self.api_key = ""
        self.is_api_key_valid = False
        self.ai_suggestions = []
        self.model_type = "openai"  # "openai" or "gemini"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def validate_api_key(self, key, model_type="openai", base_url=None):
        if not key:
            return False, "API Key Required"

        self.api_key = key
        self.model_type = model_type
        self.base_url = base_url

        try:
            # Initialize OpenAI client with the provided key
            if self.model_type == "gemini" and self.base_url:
                self.client = openai.OpenAI(
                    api_key=self.api_key, base_url=self.base_url
                )
            else:
                self.client = openai.OpenAI(api_key=self.api_key)

            # Simple test call to validate the API key
            model = "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, this is a test message. Please respond with 'API key is valid'.",
                    }
                ],
                max_tokens=10,
            )

            if "API key is valid" in response.choices[0].message.content:
                self.is_api_key_valid = True
                return True, "API key validated successfully!"
            else:
                self.is_api_key_valid = False
                return False, "Could not validate API key. Please check and try again."

        except Exception as e:
            self.is_api_key_valid = False
            return False, f"Error validating API key: {str(e)}"

    def get_productivity_suggestion(self, current_task, stats):
        if not self.is_api_key_valid:
            return None, "API key not validated"

        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            The user is currently working on: "{current_task if current_task else 'an unknown task'}".
            Today they have completed {stats['pomodoros_completed']} pomodoros and worked for {stats['focus_time']} minutes total.
            
            Provide a short, helpful productivity tip or motivational message to help them stay focused and effective.
            Keep your response concise (under 120 words) and directly actionable.
            Be encouraging but not overly enthusiastic. Sound like a knowledgeable productivity coach.
            """

            model = "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
            )

            suggestion = response.choices[0].message.content.strip()

            # Add to suggestions list
            self.ai_suggestions.append(
                {"time": datetime.now().strftime("%H:%M"), "suggestion": suggestion}
            )

            return suggestion, None

        except Exception as e:
            return None, f"Error getting AI suggestion: {str(e)}"

    def get_break_suggestion(self, focus_time):
        if not self.is_api_key_valid:
            return None, "API key not validated"

        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            The user just completed a {focus_time} minute work session.
            They're now on a break.
            
            Suggest a quick break activity that will help them refresh their mind and be ready for the next work session.
            Keep your response concise (under 100 words) and make the suggestion specific.
            """

            model = "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
            )

            suggestion = response.choices[0].message.content.strip()
            return suggestion, None

        except Exception as e:
            return None, f"Error getting break suggestion: {str(e)}"

    def analyze_productivity(self, stats, current_task, tasks):
        if not self.is_api_key_valid:
            return None, "API key not validated"

        try:
            task_text = "\n".join([f"- {task}" for task in tasks])

            prompt = f"""You are a productivity assistant in a timer app. 
            Analyze the user's current productivity based on this data:
            
            - Focus time today: {stats['focus_time']} minutes
            - Pomodoros completed: {stats['pomodoros_completed']}
            - Tasks completed: {stats['tasks_completed']}
            
            Current task: "{current_task if current_task else 'None'}"
            
            Task list:
            {task_text if task_text else "No tasks added yet."}
            
            Provide a brief analysis of their productivity patterns and one specific suggestion to improve.
            Keep your response to about 150 words. Be insightful but practical.
            """

            model = "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )

            analysis = response.choices[0].message.content.strip()
            return analysis, None

        except Exception as e:
            return None, f"Error analyzing productivity: {str(e)}"

    def generate_tasks(self, context):
        if not self.is_api_key_valid:
            return None, "API key not validated"

        if not context:
            return None, "Context required"

        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            The user is working on: "{context}"
            
            Generate 5-7 specific, actionable tasks that would help them make progress on this work.
            Each task should be:
            1. Clear and specific
            2. Small enough to complete in one focused session (25-50 minutes)
            3. Start with an action verb
            
            Format the tasks as a simple list with no explanations or additional text.
            """

            model = "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
            )

            task_suggestions = response.choices[0].message.content.strip()

            # Parse tasks from response
            new_tasks = []
            for line in task_suggestions.split("\n"):
                # Remove leading numbers, dashes, etc.
                clean_line = line.strip()
                if clean_line:
                    # Remove leading number or bullet point
                    if (
                        clean_line[0].isdigit()
                        and len(clean_line) > 2
                        and clean_line[1:3] in [". ", "- ", ") "]
                    ):
                        clean_line = clean_line[3:].strip()
                    elif clean_line[0] in ["-", "*", "•"]:
                        clean_line = clean_line[1:].strip()

                    if clean_line:
                        new_tasks.append(clean_line)

            return new_tasks, None

        except Exception as e:
            return None, f"Error generating tasks: {str(e)}"

    def get_productivity_insights(self, stats):
        if not self.is_api_key_valid:
            return None, "API key not validated"

        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            Analyze the user's productivity stats:
            
            - Focus time today: {stats['focus_time']} minutes
            - Pomodoros completed: {stats['pomodoros_completed']}
            - Tasks completed: {stats['tasks_completed']}
            
            Provide data-driven insights about their productivity patterns and suggest
            2-3 specific strategies to improve their productivity based on these numbers.
            
            If they've spent significant time but completed few tasks, suggest ways to break down work.
            If they've completed many short sessions, suggest longer focus periods.
            
            Be specific, actionable, and encouraging.
            """

            model = "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )

            insights = response.choices[0].message.content.strip()
            return insights, None

        except Exception as e:
            return None, f"Error getting AI insights: {str(e)}"

    def get_settings_dict(self):
        return {
            "api_key": self.api_key,
            "model_type": self.model_type,
            "base_url": self.base_url,
        }

    def load_from_settings(self, settings):
        self.api_key = settings.get("api_key", "")
        self.model_type = settings.get("model_type", "openai")
        self.base_url = settings.get("base_url", None)


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
