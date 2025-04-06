import sys
import time
import threading
import openai
import json
import pygame
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QTextEdit, QWidget, QTabWidget, QComboBox,
                           QSlider, QProgressBar, QMessageBox, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction

class AITimer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Productivity Timer")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize OpenAI client
        self.client = None
        self.api_key = ""
        self.is_api_key_valid = False
        
        # Initialize pygame for sounds
        pygame.mixer.init()
        
        # Timer variables
        self.remaining_time = 0
        self.timer_active = False
        self.timer_paused = False
        self.pomodoro_count = 0
        self.current_mode = "Work"  # "Work" or "Break"
        
        # Stats tracking
        self.daily_stats = {
            "focus_time": 0,
            "tasks_completed": 0,
            "pomodoros_completed": 0
        }
        
        # Task list
        self.tasks = []
        self.current_task = ""
        
        # AI suggestions
        self.ai_suggestions = []
        
        # Set up the UI
        self.setup_ui()
        
        # Create system tray icon
        self.setup_system_tray()
        
        # Set up timers
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        # Load saved settings if available
        self.load_settings()
        
    def setup_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Tab 1: Timer
        timer_tab = QWidget()
        timer_layout = QVBoxLayout(timer_tab)
        
        # API Key section
        api_layout = QHBoxLayout()
        api_label = QLabel("OpenAI API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_validate_btn = QPushButton("Validate")
        self.api_validate_btn.clicked.connect(self.validate_api_key)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(self.api_validate_btn)
        timer_layout.addLayout(api_layout)
        
        # Timer display
        self.time_display = QLabel("25:00")
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_display.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        timer_layout.addWidget(self.time_display)
        
        # Mode indicator
        self.mode_label = QLabel("Work Mode")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setFont(QFont("Arial", 14))
        timer_layout.addWidget(self.mode_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        timer_layout.addWidget(self.progress_bar)
        
        # Current task
        task_layout = QHBoxLayout()
        task_label = QLabel("Current Task:")
        self.task_input = QLineEdit()
        task_layout.addWidget(task_label)
        task_layout.addWidget(self.task_input)
        timer_layout.addLayout(task_layout)
        
        # Timer controls
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        
        self.skip_button = QPushButton("Skip")
        self.skip_button.clicked.connect(self.skip_timer)
        self.skip_button.setEnabled(False)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.skip_button)
        timer_layout.addLayout(controls_layout)
        
        # Timer modes
        modes_layout = QHBoxLayout()
        
        mode_label = QLabel("Mode:")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Pomodoro (25/5)", "Long Focus (50/10)", "Custom"])
        
        self.work_time_input = QLineEdit("25")
        self.work_time_input.setMaximumWidth(50)
        self.break_time_input = QLineEdit("5")
        self.break_time_input.setMaximumWidth(50)
        
        modes_layout.addWidget(mode_label)
        modes_layout.addWidget(self.mode_selector)
        modes_layout.addWidget(QLabel("Work:"))
        modes_layout.addWidget(self.work_time_input)
        modes_layout.addWidget(QLabel("Break:"))
        modes_layout.addWidget(self.break_time_input)
        
        timer_layout.addLayout(modes_layout)
        
        # AI Suggestions
        self.ai_suggestion_label = QLabel("AI Productivity Assistant")
        self.ai_suggestion_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        timer_layout.addWidget(self.ai_suggestion_label)
        
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setPlaceholderText("AI suggestions will appear here once you validate your API key and start working.")
        timer_layout.addWidget(self.ai_text)
        
        # AI Controls
        ai_controls = QHBoxLayout()
        self.get_suggestion_btn = QPushButton("Get Productivity Tip")
        self.get_suggestion_btn.clicked.connect(self.get_ai_suggestion)
        self.get_suggestion_btn.setEnabled(False)
        
        self.analyze_btn = QPushButton("Analyze My Productivity")
        self.analyze_btn.clicked.connect(self.analyze_productivity)
        self.analyze_btn.setEnabled(False)
        
        ai_controls.addWidget(self.get_suggestion_btn)
        ai_controls.addWidget(self.analyze_btn)
        timer_layout.addLayout(ai_controls)
        
        # Tab 2: Tasks
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        
        self.tasks_label = QLabel("Task List")
        self.tasks_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        tasks_layout.addWidget(self.tasks_label)
        
        # Add task controls
        add_task_layout = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Enter a new task...")
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.clicked.connect(self.add_task)
        
        add_task_layout.addWidget(self.new_task_input)
        add_task_layout.addWidget(self.add_task_btn)
        tasks_layout.addLayout(add_task_layout)
        
        # AI task generation
        ai_task_layout = QHBoxLayout()
        self.ai_task_btn = QPushButton("Generate Tasks with AI")
        self.ai_task_btn.clicked.connect(self.generate_tasks_with_ai)
        self.ai_task_btn.setEnabled(False)
        
        self.task_context_input = QLineEdit()
        self.task_context_input.setPlaceholderText("What are you working on? (context for AI)")
        
        ai_task_layout.addWidget(self.task_context_input)
        ai_task_layout.addWidget(self.ai_task_btn)
        tasks_layout.addLayout(ai_task_layout)
        
        # Task list
        self.task_list = QTextEdit()
        self.task_list.setReadOnly(True)
        tasks_layout.addWidget(self.task_list)
        
        # Tab 3: Statistics
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        self.stats_label = QLabel("Productivity Statistics")
        self.stats_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        stats_layout.addWidget(self.stats_label)
        
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        stats_layout.addWidget(self.stats_display)
        
        self.ai_insights_btn = QPushButton("Get AI Insights on Your Productivity")
        self.ai_insights_btn.clicked.connect(self.get_ai_insights)
        self.ai_insights_btn.setEnabled(False)
        stats_layout.addWidget(self.ai_insights_btn)
        
        # Add tabs to tab widget
        tabs.addTab(timer_tab, "Timer")
        tabs.addTab(tasks_tab, "Tasks")
        tabs.addTab(stats_tab, "Statistics")
        
        # Update stats display
        self.update_stats_display()
        
    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("alarm-clock"))
        
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def validate_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "API Key Required", "Please enter your OpenAI API key.")
            return
        
        self.api_key = key
        
        try:
            # Initialize OpenAI client with the provided key
            self.client = openai.OpenAI(api_key=self.api_key)
            
            # Simple test call to validate the API key
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, this is a test message. Please respond with 'API key is valid'."}],
                max_tokens=10
            )
            
            if "API key is valid" in response.choices[0].message.content:
                self.is_api_key_valid = True
                QMessageBox.information(self, "Success", "API key validated successfully!")
                self.get_suggestion_btn.setEnabled(True)
                self.analyze_btn.setEnabled(True)
                self.ai_task_btn.setEnabled(True)
                self.ai_insights_btn.setEnabled(True)
                
                # Display welcome message
                self.ai_text.setText("Welcome to AI Productivity Timer! I'm here to help you stay focused and productive. Start your timer to begin working, and I'll provide helpful suggestions along the way.")
                
                # Save API key
                self.save_settings()
            else:
                self.is_api_key_valid = False
                QMessageBox.warning(self, "Validation Failed", "Could not validate API key. Please check and try again.")
        
        except Exception as e:
            self.is_api_key_valid = False
            QMessageBox.warning(self, "Validation Error", f"Error validating API key: {str(e)}")
    
    def start_timer(self):
        if self.timer_active and self.timer_paused:
            # Resume timer
            self.countdown_timer.start(1000)
            self.timer_paused = False
            self.pause_button.setText("Pause")
        else:
            # Start new timer
            self.current_task = self.task_input.text()
            
            # Set timer duration based on selected mode
            mode = self.mode_selector.currentText()
            if mode == "Custom":
                try:
                    if self.current_mode == "Work":
                        minutes = int(self.work_time_input.text())
                    else:
                        minutes = int(self.break_time_input.text())
                except ValueError:
                    QMessageBox.warning(self, "Invalid Time", "Please enter valid time in minutes.")
                    return
            elif mode == "Pomodoro (25/5)":
                minutes = 25 if self.current_mode == "Work" else 5
            elif mode == "Long Focus (50/10)":
                minutes = 50 if self.current_mode == "Work" else 10
            
            self.remaining_time = minutes * 60
            self.timer_active = True
            self.timer_paused = False
            
            # Update UI
            self.update_time_display()
            self.progress_bar.setMaximum(self.remaining_time)
            self.progress_bar.setValue(self.remaining_time)
            
            # Start timer
            self.countdown_timer.start(1000)
            self.start_button.setText("Reset")
            self.pause_button.setEnabled(True)
            self.skip_button.setEnabled(True)
            
            # Get AI suggestion if API key is valid
            if self.is_api_key_valid and self.current_mode == "Work":
                threading.Thread(target=self.get_ai_suggestion).start()
    
    def pause_timer(self):
        if not self.timer_active:
            return
        
        if self.timer_paused:
            # Resume timer
            self.countdown_timer.start(1000)
            self.timer_paused = False
            self.pause_button.setText("Pause")
        else:
            # Pause timer
            self.countdown_timer.stop()
            self.timer_paused = True
            self.pause_button.setText("Resume")
    
    def skip_timer(self):
        if not self.timer_active:
            return
        
        self.timer_active = False
        self.timer_paused = False
        self.countdown_timer.stop()
        
        # Switch modes
        self.toggle_mode()
        
        # Reset UI
        self.start_button.setText("Start")
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        
        # Update time display for the next timer
        self.update_time_display_for_next_timer()
    
    def update_countdown(self):
        if self.remaining_time <= 0:
            self.timer_complete()
            return
        
        self.remaining_time -= 1
        self.update_time_display()
        self.progress_bar.setValue(self.remaining_time)
        
        # Get AI suggestion randomly during work sessions (5% chance each minute)
        if self.is_api_key_valid and self.current_mode == "Work" and self.remaining_time % 60 == 0:
            if self.remaining_time > 0 and self.current_mode == "Work" and random.random() < 0.05:
                threading.Thread(target=self.get_ai_suggestion).start()
    
    def timer_complete(self):
        self.countdown_timer.stop()
        self.timer_active = False
        
        # Play sound
        self.play_timer_complete_sound()
        
        # Update stats
        if self.current_mode == "Work":
            mode = self.mode_selector.currentText()
            if mode == "Custom":
                try:
                    minutes = int(self.work_time_input.text())
                except ValueError:
                    minutes = 25
            elif mode == "Pomodoro (25/5)":
                minutes = 25
            elif mode == "Long Focus (50/10)":
                minutes = 50
                
            self.daily_stats["focus_time"] += minutes
            self.pomodoro_count += 1
            self.daily_stats["pomodoros_completed"] += 1
            
            # Mark task as completed if there is one
            if self.current_task:
                self.complete_current_task()
        
        # Show notification
        mode_text = "work session" if self.current_mode == "Work" else "break"
        self.tray_icon.showMessage(
            f"{mode_text.capitalize()} Complete", 
            f"Your {mode_text} has ended.", 
            QSystemTrayIcon.MessageIcon.Information, 
            3000
        )
        
        # Toggle mode
        self.toggle_mode()
        
        # Reset UI
        self.start_button.setText("Start")
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        
        # Update time display for the next timer
        self.update_time_display_for_next_timer()
        
        # Update stats display
        self.update_stats_display()
        
        # Get AI suggestion after completing work session
        if self.is_api_key_valid and self.current_mode == "Break":
            threading.Thread(target=self.get_break_suggestion).start()
        
        # Save settings
        self.save_settings()
    
    def play_timer_complete_sound(self):
        try:
            sound_file = "notification.wav"  # You would need to include this file with your application
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except:
            print("Could not play sound")
    
    def toggle_mode(self):
        if self.current_mode == "Work":
            self.current_mode = "Break"
            self.mode_label.setText("Break Mode")
            self.mode_label.setStyleSheet("color: green;")
        else:
            self.current_mode = "Work"
            self.mode_label.setText("Work Mode")
            self.mode_label.setStyleSheet("color: red;")
    
    def update_time_display(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
    
    def update_time_display_for_next_timer(self):
        mode = self.mode_selector.currentText()
        if mode == "Custom":
            try:
                if self.current_mode == "Work":
                    minutes = int(self.work_time_input.text())
                else:
                    minutes = int(self.break_time_input.text())
            except ValueError:
                minutes = 25 if self.current_mode == "Work" else 5
        elif mode == "Pomodoro (25/5)":
            minutes = 25 if self.current_mode == "Work" else 5
        elif mode == "Long Focus (50/10)":
            minutes = 50 if self.current_mode == "Work" else 10
        
        self.remaining_time = minutes * 60
        self.update_time_display()
        self.progress_bar.setMaximum(self.remaining_time)
        self.progress_bar.setValue(self.remaining_time)
    
    def get_ai_suggestion(self):
        if not self.is_api_key_valid:
            return
        
        self.ai_text.clear()
        self.ai_text.setPlaceholderText("Getting AI suggestion...")
        
        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            The user is currently working on: "{self.current_task if self.current_task else 'an unknown task'}".
            Today they have completed {self.daily_stats['pomodoros_completed']} pomodoros and worked for {self.daily_stats['focus_time']} minutes total.
            
            Provide a short, helpful productivity tip or motivational message to help them stay focused and effective.
            Keep your response concise (under 120 words) and directly actionable.
            Be encouraging but not overly enthusiastic. Sound like a knowledgeable productivity coach.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            suggestion = response.choices[0].message.content.strip()
            self.ai_text.setText(suggestion)
            
            # Add to suggestions list
            self.ai_suggestions.append({
                "time": datetime.now().strftime("%H:%M"),
                "suggestion": suggestion
            })
            
        except Exception as e:
            self.ai_text.setText(f"Error getting AI suggestion: {str(e)}")
    
    def get_break_suggestion(self):
        if not self.is_api_key_valid:
            return
        
        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            The user just completed a {self.daily_stats['focus_time']} minute work session.
            They're now on a break.
            
            Suggest a quick break activity that will help them refresh their mind and be ready for the next work session.
            Keep your response concise (under 100 words) and make the suggestion specific.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            suggestion = response.choices[0].message.content.strip()
            self.ai_text.setText(suggestion)
            
        except Exception as e:
            self.ai_text.setText(f"Error getting break suggestion: {str(e)}")
    
    def analyze_productivity(self):
        if not self.is_api_key_valid:
            return
        
        self.ai_text.clear()
        self.ai_text.setPlaceholderText("Analyzing your productivity...")
        
        try:
            task_text = "\n".join([f"- {task}" for task in self.tasks])
            
            prompt = f"""You are a productivity assistant in a timer app. 
            Analyze the user's current productivity based on this data:
            
            - Focus time today: {self.daily_stats['focus_time']} minutes
            - Pomodoros completed: {self.daily_stats['pomodoros_completed']}
            - Tasks completed: {self.daily_stats['tasks_completed']}
            
            Current task: "{self.current_task if self.current_task else 'None'}"
            
            Task list:
            {task_text if task_text else "No tasks added yet."}
            
            Provide a brief analysis of their productivity patterns and one specific suggestion to improve.
            Keep your response to about 150 words. Be insightful but practical.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            analysis = response.choices[0].message.content.strip()
            self.ai_text.setText(analysis)
            
        except Exception as e:
            self.ai_text.setText(f"Error analyzing productivity: {str(e)}")
    
    def add_task(self):
        task = self.new_task_input.text().strip()
        if not task:
            return
        
        self.tasks.append(task)
        self.new_task_input.clear()
        self.update_task_list()
        
        # If no current task is set, use this task
        if not self.task_input.text():
            self.task_input.setText(task)
    
    def complete_current_task(self):
        if not self.current_task:
            return
            
        # Check if the current task is in the task list
        if self.current_task in self.tasks:
            self.tasks.remove(self.current_task)
            self.daily_stats["tasks_completed"] += 1
            self.update_task_list()
        
        # Clear current task
        self.task_input.clear()
        self.current_task = ""
    
    def update_task_list(self):
        if not self.tasks:
            self.task_list.setText("No tasks added yet.")
            return
            
        task_text = ""
        for i, task in enumerate(self.tasks, 1):
            task_text += f"{i}. {task}\n"
            
        self.task_list.setText(task_text)
    
    def generate_tasks_with_ai(self):
        if not self.is_api_key_valid:
            return
            
        context = self.task_context_input.text().strip()
        if not context:
            QMessageBox.warning(self, "Context Required", "Please enter some context about what you're working on.")
            return
            
        self.task_list.setPlaceholderText("Generating tasks with AI...")
        
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
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250
            )
            
            task_suggestions = response.choices[0].message.content.strip()
            
            # Parse tasks from response
            new_tasks = []
            for line in task_suggestions.split('\n'):
                # Remove leading numbers, dashes, etc.
                clean_line = line.strip()
                if clean_line:
                    # Remove leading number or bullet point
                    if clean_line[0].isdigit() and len(clean_line) > 2 and clean_line[1:3] in ['. ', '- ', ') ']:
                        clean_line = clean_line[3:].strip()
                    elif clean_line[0] in ['-', '*', '•']:
                        clean_line = clean_line[1:].strip()
                    
                    if clean_line:
                        new_tasks.append(clean_line)
            
            # Add new tasks to list
            self.tasks.extend(new_tasks)
            self.update_task_list()
            
            # If no current task is set, use the first task
            if not self.task_input.text() and new_tasks:
                self.task_input.setText(new_tasks[0])
                
            QMessageBox.information(self, "Tasks Generated", f"Successfully generated {len(new_tasks)} tasks.")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error generating tasks: {str(e)}")
    
    def update_stats_display(self):
        stats_text = f"""
        Today's Productivity Stats:
        ---------------------------
        Focus time: {self.daily_stats['focus_time']} minutes
        Pomodoros completed: {self.daily_stats['pomodoros_completed']}
        Tasks completed: {self.daily_stats['tasks_completed']}
        
        Current task: {self.current_task if self.current_task else "None"}
        """
        
        self.stats_display.setText(stats_text)
    
    def get_ai_insights(self):
        if not self.is_api_key_valid:
            return
            
        try:
            prompt = f"""You are a productivity assistant in a timer app. 
            Analyze the user's productivity stats:
            
            - Focus time today: {self.daily_stats['focus_time']} minutes
            - Pomodoros completed: {self.daily_stats['pomodoros_completed']}
            - Tasks completed: {self.daily_stats['tasks_completed']}
            
            Provide data-driven insights about their productivity patterns and suggest
            2-3 specific strategies to improve their productivity based on these numbers.
            
            If they've spent significant time but completed few tasks, suggest ways to break down work.
            If they've completed many short sessions, suggest longer focus periods.
            
            Be specific, actionable, and encouraging.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            insights = response.choices[0].message.content.strip()
            
            # Display in a message box
            msg_box = QMessageBox()
            msg_box.setWindowTitle("AI Productivity Insights")
            msg_box.setText(insights)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error getting AI insights: {str(e)}")
    
    def save_settings(self):
        settings = {
            "api_key": self.api_key,
            "daily_stats": self.daily_stats,
            "tasks": self.tasks,
            "pomodoro_count": self.pomodoro_count,
            "work_time": self.work_time_input.text(),
            "break_time": self.break_time_input.text(),
            "mode_index": self.mode_selector.currentIndex()
        }
        
        try:
            with open("ai_timer_settings.json", "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
    
    def load_settings(self):
        try:
            with open("ai_timer_settings.json", "r") as f:
                settings = json.load(f)
                
            self.api_key = settings.get("api_key", "")
            self.api_key_input.setText(self.api_key)
            
            if self.api_key:
                self.validate_api_key()
                
            self.daily_stats = settings.get("daily_stats", {"focus_time": 0, "tasks_completed": 0, "pomodoros_completed": 0})
            self.tasks = settings.get("tasks", [])
            self.pomodoro_count = settings.get("pomodoro_count", 0)
            
            self.work_time_input.setText(settings.get("work_time", "25"))
            self.break_time_input.setText(settings.get("break_time", "5"))
            self.mode_selector.setCurrentIndex(settings.get("mode_index", 0))
            
            # Update displays
            self.update_task_list()
            self.update_stats_display()
            self.update_time_display_for_next_timer()
            
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
    
    def closeEvent(self, event):
        # Save settings before closing
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    # Add missing import
    import random
    
    app = QApplication(sys.argv)
    window = AITimer()
    window.show()
    sys.exit(app.exec())