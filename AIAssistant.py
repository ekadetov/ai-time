import openai


from datetime import datetime


class AIAssistant:
    def __init__(self):
        self.client = None
        self.api_key = ""
        self.is_api_key_valid = False
        self.ai_suggestions = []
        self.model_type = "gemini"  # "openai" or "gemini"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.current_model = "gpt-3.5-turbo"  # Default model

    def validate_api_key(self, key, model_type="openai", base_url=None):
        if not key:
            return False, "API Key Required"

        self.api_key = key
        self.model_type = model_type
        self.base_url = base_url
        # Set the model based on model_type
        self.current_model = (
            "gemini-2.0-flash" if self.model_type == "gemini" else "gpt-3.5-turbo"
        )

        try:
            # Initialize OpenAI client with the provided key
            if self.model_type == "gemini" and self.base_url:
                self.client = openai.OpenAI(
                    api_key=self.api_key, base_url=self.base_url
                )
            else:
                self.client = openai.OpenAI(api_key=self.api_key)

            # Simple test call to validate the API key
            response = self.client.chat.completions.create(
                model=self.current_model,
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

            response = self.client.chat.completions.create(
                model=self.current_model,
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

            response = self.client.chat.completions.create(
                model=self.current_model,
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

            response = self.client.chat.completions.create(
                model=self.current_model,
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

            response = self.client.chat.completions.create(
                model=self.current_model,
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
                        clean_line = clean_line[3:].trip()
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

            response = self.client.chat.completions.create(
                model=self.current_model,
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
        # Update current_model when loading settings
        self.current_model = (
            "gemini-pro" if self.model_type == "gemini" else "gpt-3.5-turbo"
        )
