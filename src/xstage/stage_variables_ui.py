"""
Stage Variables UI
Display and edit stage variables
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QGroupBox, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from typing import Optional

from .stage_variables import StageVariableManager


class StageVariablesWidget(QWidget):
    """Widget for managing stage variables"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variable_manager = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Stage Variables</b>")
        layout.addWidget(title)
        
        # Variables table
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(2)
        self.variables_table.setHorizontalHeaderLabels(["Variable", "Value"])
        self.variables_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.variables_table)
        
        # Add variable
        add_group = QGroupBox("Add/Edit Variable")
        add_layout = QFormLayout()
        
        self.var_name_edit = QLineEdit()
        self.var_name_edit.setPlaceholderText("Variable name (e.g., ASSET)")
        add_layout.addRow("Name:", self.var_name_edit)
        
        self.var_value_edit = QLineEdit()
        self.var_value_edit.setPlaceholderText("Variable value")
        add_layout.addRow("Value:", self.var_value_edit)
        
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add/Update")
        add_btn.clicked.connect(self.add_variable)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_variable)
        button_layout.addWidget(remove_btn)
        
        add_layout.addRow("", button_layout)
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        if stage:
            self.variable_manager = StageVariableManager(stage)
            self.refresh()
        else:
            self.variable_manager = None
            self.variables_table.setRowCount(0)
    
    def refresh(self):
        """Refresh variables table"""
        self.variables_table.setRowCount(0)
        
        if not self.variable_manager:
            return
        
        variables = self.variable_manager.get_stage_variables()
        self.variables_table.setRowCount(len(variables))
        
        row = 0
        for name, value in variables.items():
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.variables_table.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(str(value))
            self.variables_table.setItem(row, 1, value_item)
            row += 1
    
    def add_variable(self):
        """Add or update a variable"""
        if not self.variable_manager:
            return
        
        name = self.var_name_edit.text().strip()
        value = self.var_value_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Variable name cannot be empty")
            return
        
        if self.variable_manager.set_stage_variable(name, value):
            self.refresh()
            self.var_name_edit.clear()
            self.var_value_edit.clear()
        else:
            QMessageBox.critical(self, "Error", "Failed to set stage variable")
    
    def remove_variable(self):
        """Remove selected variable"""
        # Note: USD doesn't have a direct way to remove stage variables
        # This would need to be implemented by editing the layer metadata
        QMessageBox.information(self, "Info", "Variable removal requires editing layer metadata directly")

