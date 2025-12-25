"""
Converter UI - Pipeline-friendly conversion interface
Easy-to-use dialog for converting 3D files to USD
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QGroupBox, QFormLayout, QComboBox,
    QDoubleSpinBox, QCheckBox, QProgressBar, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
from typing import Optional

from .converter import USDConverter, ConversionOptions


class ConversionThread(QThread):
    """Thread for running conversion in background"""
    
    progress = Signal(int, str)  # progress, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, converter: USDConverter, input_path: str, output_path: str):
        super().__init__()
        self.converter = converter
        self.input_path = input_path
        self.output_path = output_path
    
    def run(self):
        """Run conversion"""
        def progress_callback(progress, message):
            self.progress.emit(progress, message)
        
        try:
            success = self.converter.convert(
                self.input_path,
                self.output_path,
                progress_callback
            )
            if success:
                self.finished.emit(True, f"Conversion complete: {self.output_path}")
            else:
                self.finished.emit(False, "Conversion failed")
        except Exception as e:
            self.finished.emit(False, f"Conversion error: {str(e)}")


class ConverterDialog(QDialog):
    """Dialog for converting 3D files to USD"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Convert to USD")
        self.setMinimumWidth(600)
        self.conversion_thread = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<h2>Convert 3D File to USD</h2>")
        layout.addWidget(title)
        
        # File selection
        file_group = QGroupBox("File Selection")
        file_layout = QFormLayout()
        
        # Input file
        input_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Select input file...")
        input_layout.addWidget(self.input_path_edit)
        
        input_btn = QPushButton("Browse...")
        input_btn.clicked.connect(self.browse_input)
        input_layout.addWidget(input_btn)
        file_layout.addRow("Input File:", input_layout)
        
        # Output file
        output_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Output USD file...")
        output_layout.addWidget(self.output_path_edit)
        
        output_btn = QPushButton("Browse...")
        output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(output_btn)
        file_layout.addRow("Output File:", output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Conversion options
        options_group = QGroupBox("Conversion Options")
        options_layout = QFormLayout()
        
        # Up axis
        self.up_axis_combo = QComboBox()
        self.up_axis_combo.addItems(['Y', 'Z'])
        self.up_axis_combo.setCurrentText('Y')
        options_layout.addRow("Up Axis:", self.up_axis_combo)
        
        # Scale
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.001, 1000.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setDecimals(3)
        options_layout.addRow("Scale Factor:", self.scale_spin)
        
        # Meters per unit
        self.meters_per_unit_spin = QDoubleSpinBox()
        self.meters_per_unit_spin.setRange(0.001, 1000.0)
        self.meters_per_unit_spin.setValue(1.0)
        self.meters_per_unit_spin.setDecimals(3)
        options_layout.addRow("Meters Per Unit:", self.meters_per_unit_spin)
        
        # Export options
        self.export_materials_check = QCheckBox()
        self.export_materials_check.setChecked(True)
        options_layout.addRow("Export Materials:", self.export_materials_check)
        
        self.export_normals_check = QCheckBox()
        self.export_normals_check.setChecked(True)
        options_layout.addRow("Export Normals:", self.export_normals_check)
        
        self.export_uvs_check = QCheckBox()
        self.export_uvs_check.setChecked(True)
        options_layout.addRow("Export UVs:", self.export_uvs_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.clicked.connect(self.start_conversion)
        button_layout.addWidget(self.convert_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_input(self):
        """Browse for input file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "",
            "3D Files (*.fbx *.obj *.abc *.gltf *.glb *.stl *.ply *.dae *.3ds);;"
            "FBX (*.fbx);;OBJ (*.obj);;Alembic (*.abc);;glTF (*.gltf *.glb);;"
            "STL (*.stl);;PLY (*.ply);;All Files (*)"
        )
        
        if file_path:
            self.input_path_edit.setText(file_path)
            # Auto-generate output path
            if not self.output_path_edit.text():
                input_path = Path(file_path)
                output_path = input_path.with_suffix('.usd')
                self.output_path_edit.setText(str(output_path))
    
    def browse_output(self):
        """Browse for output file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save USD File", "",
            "USD Files (*.usd *.usda *.usdc);;All Files (*)"
        )
        
        if file_path:
            self.output_path_edit.setText(file_path)
    
    def start_conversion(self):
        """Start conversion"""
        input_path = self.input_path_edit.text()
        output_path = self.output_path_edit.text()
        
        if not input_path or not Path(input_path).exists():
            QMessageBox.warning(self, "Invalid Input", "Please select a valid input file")
            return
        
        if not output_path:
            QMessageBox.warning(self, "Invalid Output", "Please specify an output file")
            return
        
        # Create conversion options
        options = ConversionOptions(
            up_axis=self.up_axis_combo.currentText(),
            scale=self.scale_spin.value(),
            meters_per_unit=self.meters_per_unit_spin.value(),
            export_materials=self.export_materials_check.isChecked(),
            export_normals=self.export_normals_check.isChecked(),
            export_uvs=self.export_uvs_check.isChecked(),
        )
        
        # Create converter
        converter = USDConverter(options)
        
        # Start conversion thread
        self.conversion_thread = ConversionThread(converter, input_path, output_path)
        self.conversion_thread.progress.connect(self.on_progress)
        self.conversion_thread.finished.connect(self.on_finished)
        self.conversion_thread.start()
        
        # Update UI
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_text.clear()
        self.status_text.append("Starting conversion...")
    
    def on_progress(self, progress: int, message: str):
        """Handle progress update"""
        self.progress_bar.setValue(progress)
        self.status_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_finished(self, success: bool, message: str):
        """Handle conversion finished"""
        self.convert_btn.setEnabled(True)
        self.status_text.append(message)
        
        if success:
            QMessageBox.information(self, "Success", f"Conversion complete!\n\n{message}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Conversion failed!\n\n{message}")

