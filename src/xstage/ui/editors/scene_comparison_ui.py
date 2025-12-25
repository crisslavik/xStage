"""
Scene Comparison UI
Side-by-side comparison of two USD stages
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QSplitter, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from typing import Optional

from ...managers.scene_comparison import SceneComparator, SceneDiff


class SceneComparisonWidget(QWidget):
    """Widget for comparing two USD stages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage1 = None
        self.stage2 = None
        self.comparator = None
        self.diff = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Scene Comparison</b>")
        layout.addWidget(title)
        
        # File selection
        file_group = QGroupBox("Stage Files")
        file_layout = QVBoxLayout()
        
        # Stage 1
        stage1_layout = QHBoxLayout()
        stage1_layout.addWidget(QLabel("Stage 1:"))
        self.stage1_path_edit = QLineEdit()
        self.stage1_path_edit.setPlaceholderText("Select first USD file...")
        stage1_layout.addWidget(self.stage1_path_edit)
        
        stage1_btn = QPushButton("Browse...")
        stage1_btn.clicked.connect(lambda: self.browse_file(1))
        stage1_layout.addWidget(stage1_btn)
        file_layout.addLayout(stage1_layout)
        
        # Stage 2
        stage2_layout = QHBoxLayout()
        stage2_layout.addWidget(QLabel("Stage 2:"))
        self.stage2_path_edit = QLineEdit()
        self.stage2_path_edit.setPlaceholderText("Select second USD file...")
        stage2_layout.addWidget(self.stage2_path_edit)
        
        stage2_btn = QPushButton("Browse...")
        stage2_btn.clicked.connect(lambda: self.browse_file(2))
        stage2_layout.addWidget(stage2_btn)
        file_layout.addLayout(stage2_layout)
        
        compare_btn = QPushButton("Compare")
        compare_btn.clicked.connect(self.compare_stages)
        file_layout.addWidget(compare_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Comparison results
        results_group = QGroupBox("Comparison Results")
        results_layout = QVBoxLayout()
        
        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(100)
        results_layout.addWidget(self.summary_text)
        
        # Diff tree
        self.diff_tree = QTreeWidget()
        self.diff_tree.setHeaderLabels(["Difference", "Type", "Details"])
        results_layout.addWidget(self.diff_tree)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
    
    def browse_file(self, stage_num: int):
        """Browse for USD file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Stage {stage_num}",
            "", "USD Files (*.usd *.usda *.usdc *.usdz);;All Files (*)"
        )
        
        if file_path:
            if stage_num == 1:
                self.stage1_path_edit.setText(file_path)
            else:
                self.stage2_path_edit.setText(file_path)
    
    def compare_stages(self):
        """Compare the two stages"""
        stage1_path = self.stage1_path_edit.text()
        stage2_path = self.stage2_path_edit.text()
        
        if not stage1_path or not stage2_path:
            return
        
        try:
            from pxr import Usd
            
            self.stage1 = Usd.Stage.Open(stage1_path)
            self.stage2 = Usd.Stage.Open(stage2_path)
            
            if not self.stage1 or not self.stage2:
                return
            
            self.comparator = SceneComparator(self.stage1, self.stage2)
            self.diff = self.comparator.compare()
            
            # Display results
            self.display_diff()
        except Exception as e:
            self.summary_text.setText(f"Error comparing stages: {e}")
    
    def display_diff(self):
        """Display comparison results"""
        if not self.diff:
            return
        
        # Summary
        summary = self.comparator.get_diff_summary(self.diff)
        self.summary_text.setText(summary)
        
        # Diff tree
        self.diff_tree.clear()
        
        # Added prims
        if self.diff.added_prims:
            added_item = QTreeWidgetItem(["Added Prims", str(len(self.diff.added_prims)), ""])
            for prim_path in self.diff.added_prims:
                child = QTreeWidgetItem([prim_path, "Added Prim", ""])
                added_item.addChild(child)
            self.diff_tree.addTopLevelItem(added_item)
        
        # Removed prims
        if self.diff.removed_prims:
            removed_item = QTreeWidgetItem(["Removed Prims", str(len(self.diff.removed_prims)), ""])
            for prim_path in self.diff.removed_prims:
                child = QTreeWidgetItem([prim_path, "Removed Prim", ""])
                removed_item.addChild(child)
            self.diff_tree.addTopLevelItem(removed_item)
        
        # Modified prims
        if self.diff.modified_prims:
            modified_item = QTreeWidgetItem(["Modified Prims", str(len(self.diff.modified_prims)), ""])
            for prim_path in self.diff.modified_prims:
                child = QTreeWidgetItem([prim_path, "Modified Prim", ""])
                modified_item.addChild(child)
            self.diff_tree.addTopLevelItem(modified_item)
        
        # Modified attributes
        if self.diff.modified_attributes:
            attrs_item = QTreeWidgetItem(["Modified Attributes", "", ""])
            for prim_path, attrs in self.diff.modified_attributes.items():
                prim_item = QTreeWidgetItem([prim_path, "Prim", ""])
                for attr_name in attrs:
                    old_val, new_val = self.diff.different_values.get(prim_path, {}).get(attr_name, (None, None))
                    details = f"Old: {old_val}, New: {new_val}"
                    attr_item = QTreeWidgetItem([attr_name, "Attribute", details])
                    prim_item.addChild(attr_item)
                attrs_item.addChild(prim_item)
            self.diff_tree.addTopLevelItem(attrs_item)
        
        self.diff_tree.expandAll()

