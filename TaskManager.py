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
