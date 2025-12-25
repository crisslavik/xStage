"""
Progress Reporting System
Pipeline-friendly progress reporting for long operations
"""

from PySide6.QtWidgets import QProgressDialog, QLabel
from PySide6.QtCore import Qt, QThread, Signal, QObject
from typing import Optional, Callable


class ProgressReporter(QObject):
    """Progress reporter for long operations"""
    
    progress = Signal(int, str)  # progress (0-100), message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_progress = 0
        self.current_message = ""
    
    def report(self, progress: int, message: str = ""):
        """Report progress"""
        self.current_progress = progress
        self.current_message = message
        self.progress.emit(progress, message)
    
    def finish(self, success: bool, message: str = ""):
        """Report completion"""
        self.finished.emit(success, message)


class ProgressDialogManager:
    """Manages progress dialogs for operations"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.current_dialog = None
    
    def show_progress(self, title: str = "Processing...", 
                     cancelable: bool = True) -> ProgressReporter:
        """Show progress dialog and return reporter"""
        self.current_dialog = QProgressDialog(title, "Cancel", 0, 100, self.parent)
        self.current_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.current_dialog.setAutoClose(True)
        self.current_dialog.setAutoReset(True)
        self.current_dialog.show()
        
        reporter = ProgressReporter()
        reporter.progress.connect(self._on_progress)
        reporter.finished.connect(self._on_finished)
        
        return reporter
    
    def _on_progress(self, progress: int, message: str):
        """Handle progress update"""
        if self.current_dialog:
            self.current_dialog.setValue(progress)
            if message:
                self.current_dialog.setLabelText(message)
    
    def _on_finished(self, success: bool, message: str):
        """Handle completion"""
        if self.current_dialog:
            self.current_dialog.setValue(100)
            if message:
                self.current_dialog.setLabelText(message)
            self.current_dialog.close()
            self.current_dialog = None

