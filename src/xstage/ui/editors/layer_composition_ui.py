"""
Layer Composition UI Widget
Displays layer stack, references, subLayers, and payloads in a tree view
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel,
    QPushButton, QHBoxLayout, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt
from typing import Optional

from ...managers.layer_composition import LayerCompositionManager


class LayerCompositionWidget(QWidget):
    """Widget for displaying and managing layer composition"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.composition_manager = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("<b>Layer Composition</b>")
        layout.addWidget(title)
        
        # Layer stack tree
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderLabels(["Layer", "Type", "Path"])
        self.layer_tree.setHeaderItem(QTreeWidgetItem(["Layer", "Type", "Path"]))
        self.layer_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.layer_tree)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_stage(self, stage):
        """Set the USD stage"""
        if stage:
            self.composition_manager = LayerCompositionManager(stage)
            self.refresh()
        else:
            self.composition_manager = None
            self.layer_tree.clear()
    
    def refresh(self):
        """Refresh layer composition display"""
        self.layer_tree.clear()
        
        if not self.composition_manager:
            return
        
        # Get layer stack
        layer_stack = self.composition_manager.get_layer_stack()
        
        for layer_info in layer_stack:
            # Main layer item
            layer_item = QTreeWidgetItem([
                layer_info['display_name'] or layer_info['identifier'],
                "Root Layer" if layer_info == layer_stack[0] else "Sublayer",
                layer_info['identifier']
            ])
            layer_item.setToolTip(0, layer_info['identifier'])
            self.layer_tree.addTopLevelItem(layer_item)
            
            # Add subLayers
            if layer_info['sub_layers']:
                sublayer_header = QTreeWidgetItem(["SubLayers", "", ""])
                sublayer_header.setExpanded(True)
                layer_item.addChild(sublayer_header)
                
                for sublayer in layer_info['sub_layers']:
                    sublayer_item = QTreeWidgetItem([
                        sublayer['path'],
                        "SubLayer",
                        sublayer['path']
                    ])
                    if sublayer['offset']:
                        offset_str = f"Offset: {sublayer['offset']['offset']}, Scale: {sublayer['offset']['scale']}"
                        sublayer_item.setToolTip(0, offset_str)
                    sublayer_header.addChild(sublayer_item)
            
            # Add references
            if layer_info['references']:
                ref_header = QTreeWidgetItem(["References", "", ""])
                ref_header.setExpanded(True)
                layer_item.addChild(ref_header)
                
                for ref in layer_info['references']:
                    ref_item = QTreeWidgetItem([
                        f"{ref['prim_path']} -> {ref['asset_path'] or 'N/A'}",
                        "Reference",
                        ref['asset_path'] or 'N/A'
                    ])
                    if ref['layer_offset']:
                        offset_str = f"Offset: {ref['layer_offset']['offset']}, Scale: {ref['layer_offset']['scale']}"
                        ref_item.setToolTip(0, offset_str)
                    ref_header.addChild(ref_item)
            
            # Add payloads
            if layer_info['payloads']:
                payload_header = QTreeWidgetItem(["Payloads", "", ""])
                payload_header.setExpanded(True)
                layer_item.addChild(payload_header)
                
                for payload in layer_info['payloads']:
                    payload_item = QTreeWidgetItem([
                        f"{payload['prim_path']} -> {payload['asset_path'] or 'N/A'}",
                        "Payload",
                        payload['asset_path'] or 'N/A'
                    ])
                    payload_header.addChild(payload_item)
        
        # Expand all
        self.layer_tree.expandAll()

