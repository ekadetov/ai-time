import sys
import threading
import pygame
import random
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QWidget,
    QTabWidget,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QAction
from AIAssistant import AIAssistant
from StatsManager import StatsManager
from TaskManager import TaskManager
from TimerModel import TimerModel
from SettingsManager import SettingsManager


class AITimer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Productivity Timer")
        self.setGeometry(100, 100, 800, 600)

        # Initialize models
        self.timer_model = TimerModel()
        self.task_manager = TaskManager()
        self.stats_manager = StatsManager()
        self.ai_assistant = AIAssistant()

        # Initialize pygame for sounds
        pygame.mixer.init()

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
        self.ai_text.setPlaceholderText(
            "AI suggestions will appear here once you validate your API key and start working."
        )
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
        self.task_context_input.setPlaceholderText(
            "What are you working on? (context for AI)"
        )

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
        success, message = self.ai_assistant.validate_api_key(key)

        if success:
            QMessageBox.information(self, "Success", message)
            self.get_suggestion_btn.setEnabled(True)
            self.analyze_btn.setEnabled(True)
            self.ai_task_btn.setEnabled(True)
            self.ai_insights_btn.setEnabled(True)

            # Display welcome message
            self.ai_text.setText(
                "Welcome to AI Productivity Timer! I'm here to help you stay focused and productive. Start your timer to begin working, and I'll provide helpful suggestions along the way."
            )

            # Save API key
            self.save_settings()
        else:
            QMessageBox.warning(self, "Validation Failed", message)

    def start_timer(self):
        if self.timer_model.timer_active and self.timer_model.timer_paused:
            # Resume timer
            self.countdown_timer.start(1000)
            self.timer_model.timer_paused = False
            self.pause_button.setText("Pause")
        else:
            # Start new timer
            self.task_manager.current_task = self.task_input.text()

            # Set timer duration based on selected mode
            mode = self.mode_selector.currentText()

            remaining_time, error = self.timer_model.start_timer(
                mode, self.timer_model.current_mode
            )

            if error:
                QMessageBox.warning(self, "Invalid Time", error)
                return

            # Update UI
            self.update_time_display()
            self.progress_bar.setMaximum(self.timer_model.remaining_time)
            self.progress_bar.setValue(self.timer_model.remaining_time)

            # Start timer
            self.countdown_timer.start(1000)
            self.start_button.setText("Reset")
            self.pause_button.setEnabled(True)
            self.skip_button.setEnabled(True)

            # Get AI suggestion if API key is valid
            if (
                self.ai_assistant.is_api_key_valid
                and self.timer_model.current_mode == "Work"
            ):
                threading.Thread(target=self.get_ai_suggestion).start()

    def pause_timer(self):
        if not self.timer_model.timer_active:
            return

        is_paused = self.timer_model.pause_timer()

        if is_paused:
            # Pause timer
            self.countdown_timer.stop()
            self.pause_button.setText("Resume")
        else:
            # Resume timer
            self.countdown_timer.start(1000)
            self.pause_button.setText("Pause")

    def skip_timer(self):
        if not self.timer_model.timer_active:
            return

        success = self.timer_model.skip_timer()
        if success:
            self.countdown_timer.stop()

            # Update UI
            self.mode_label.setText(f"{self.timer_model.current_mode} Mode")
            self.mode_label.setStyleSheet(
                f"color: {'green' if self.timer_model.current_mode == 'Break' else 'red'};"
            )

            # Reset UI
            self.start_button.setText("Start")
            self.pause_button.setText("Pause")
            self.pause_button.setEnabled(False)
            self.skip_button.setEnabled(False)

            # Update time display for the next timer
            self.update_time_display_for_next_timer()

    def update_countdown(self):
        timer_complete = self.timer_model.update_countdown()

        if timer_complete:
            self.timer_complete()
            return

        self.update_time_display()
        self.progress_bar.setValue(self.timer_model.remaining_time)

        # Get AI suggestion randomly during work sessions (5% chance each minute)
        if (
            self.ai_assistant.is_api_key_valid
            and self.timer_model.current_mode == "Work"
            and self.timer_model.remaining_time % 60 == 0
        ):
            if self.timer_model.remaining_time > 0 and random.random() < 0.05:
                threading.Thread(target=self.get_ai_suggestion).start()

    def timer_complete(self):
        self.countdown_timer.stop()
        self.timer_model.timer_active = False

        # Play sound
        self.play_timer_complete_sound()

        # Update stats
        if self.timer_model.current_mode == "Work":
            mode = self.mode_selector.currentText()
            if mode == "Custom":
                try:
                    minutes = int(self.timer_model.work_time)
                except ValueError:
                    minutes = 25
            elif mode == "Pomodoro (25/5)":
                minutes = 25
            elif mode == "Long Focus (50/10)":
                minutes = 50

            self.stats_manager.update_work_completed(minutes)
            self.timer_model.pomodoro_count += 1

            # Mark task as completed if there is one
            if self.task_manager.current_task:
                self.complete_current_task()

        # Show notification
        mode_text = (
            "work session" if self.timer_model.current_mode == "Work" else "break"
        )
        self.tray_icon.showMessage(
            f"{mode_text.capitalize()} Complete",
            f"Your {mode_text} has ended.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

        # Toggle mode
        new_mode = self.timer_model.toggle_mode()
        self.mode_label.setText(f"{new_mode} Mode")
        self.mode_label.setStyleSheet(
            f"color: {'green' if new_mode == 'Break' else 'red'};"
        )

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
        if (
            self.ai_assistant.is_api_key_valid
            and self.timer_model.current_mode == "Break"
        ):
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

    def update_time_display(self):
        minutes = self.timer_model.remaining_time // 60
        seconds = self.timer_model.remaining_time % 60
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")

    def update_time_display_for_next_timer(self):
        mode = self.mode_selector.currentText()
        self.timer_model.remaining_time = self.timer_model.get_next_timer_duration(mode)
        self.update_time_display()
        self.progress_bar.setMaximum(self.timer_model.remaining_time)
        self.progress_bar.setValue(self.timer_model.remaining_time)

    def get_ai_suggestion(self):
        if not self.ai_assistant.is_api_key_valid:
            return

        self.ai_text.clear()
        self.ai_text.setPlaceholderText("Getting AI suggestion...")

        suggestion, error = self.ai_assistant.get_productivity_suggestion(
            self.task_manager.current_task, self.stats_manager.daily_stats
        )

        if suggestion:
            self.ai_text.setText(suggestion)
        else:
            self.ai_text.setText(error)

    def get_break_suggestion(self):
        if not self.ai_assistant.is_api_key_valid:
            return

        suggestion, error = self.ai_assistant.get_break_suggestion(
            self.stats_manager.daily_stats["focus_time"]
        )

        if suggestion:
            self.ai_text.setText(suggestion)
        else:
            self.ai_text.setText(error)

    def analyze_productivity(self):
        if not self.ai_assistant.is_api_key_valid:
            return

        self.ai_text.clear()
        self.ai_text.setPlaceholderText("Analyzing your productivity...")

        analysis, error = self.ai_assistant.analyze_productivity(
            self.stats_manager.daily_stats,
            self.task_manager.current_task,
            self.task_manager.tasks,
        )

        if analysis:
            self.ai_text.setText(analysis)
        else:
            self.ai_text.setText(error)

    def add_task(self):
        task = self.new_task_input.text().strip()
        success = self.task_manager.add_task(task)

        if success:
            self.new_task_input.clear()
            self.update_task_list()

            # If no current task is set, use this task
            if not self.task_input.text():
                self.task_input.setText(task)

    def complete_current_task(self):
        success = self.task_manager.complete_task(self.task_manager.current_task)

        if success:
            self.stats_manager.task_completed()
            self.update_task_list()

        # Clear current task
        self.task_input.clear()
        self.task_manager.current_task = ""

    def update_task_list(self):
        task_text = self.task_manager.get_task_list_text()
        self.task_list.setText(task_text)

    def generate_tasks_with_ai(self):
        if not self.ai_assistant.is_api_key_valid:
            return

        context = self.task_context_input.text().strip()

        self.task_list.setPlaceholderText("Generating tasks with AI...")

        new_tasks, error = self.ai_assistant.generate_tasks(context)

        if new_tasks:
            # Add new tasks to list
            for task in new_tasks:
                self.task_manager.add_task(task)

            self.update_task_list()

            # If no current task is set, use the first task
            if not self.task_input.text() and new_tasks:
                self.task_input.setText(new_tasks[0])

            QMessageBox.information(
                self,
                "Tasks Generated",
                f"Successfully generated {len(new_tasks)} tasks.",
            )
        else:
            QMessageBox.warning(self, "Error", error)

    def update_stats_display(self):
        stats_text = self.stats_manager.get_stats_text(self.task_manager.current_task)
        self.stats_display.setText(stats_text)

    def get_ai_insights(self):
        if not self.ai_assistant.is_api_key_valid:
            return

        insights, error = self.ai_assistant.get_productivity_insights(
            self.stats_manager.daily_stats
        )

        if insights:
            # Display in a message box
            msg_box = QMessageBox()
            msg_box.setWindowTitle("AI Productivity Insights")
            msg_box.setText(insights)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
        else:
            QMessageBox.warning(self, "Error", error)

    def save_settings(self):
        # Update model data from UI
        self.timer_model.work_time = self.work_time_input.text()
        self.timer_model.break_time = self.break_time_input.text()
        self.timer_model.mode_index = self.mode_selector.currentIndex()

        SettingsManager.save_settings(
            self.timer_model, self.task_manager, self.stats_manager, self.ai_assistant
        )

    def load_settings(self):
        settings = SettingsManager.load_settings()
        if not settings:
            return

        # Load settings into models
        self.timer_model.load_from_settings(settings)
        self.task_manager.load_from_settings(settings)
        self.stats_manager.load_from_settings(settings)
        self.ai_assistant.load_from_settings(settings)

        # Update UI from models
        self.api_key_input.setText(self.ai_assistant.api_key)

        if self.ai_assistant.api_key:
            self.validate_api_key()

        self.work_time_input.setText(self.timer_model.work_time)
        self.break_time_input.setText(self.timer_model.break_time)
        self.mode_selector.setCurrentIndex(self.timer_model.mode_index)

        # Update displays
        self.update_task_list()
        self.update_stats_display()
        self.update_time_display_for_next_timer()

    def closeEvent(self, event):
        # Save settings before closing
        self.save_settings()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AITimer()
    window.show()
    sys.exit(app.exec())
