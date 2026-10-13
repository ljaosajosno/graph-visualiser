from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QHBoxLayout, QWidget, QCheckBox
)

# Window to display node information
class NodeInfoWindow(QDialog):
    def __init__(self, node_data, db_handler=None, refresh_callback=None):
        super().__init__()
        self.setWindowTitle("Node Details")
        self.setGeometry(200, 200, 400, 400)
        self.node_data = node_data
        self.db_handler = db_handler
        self.refresh_callback = refresh_callback

        self.property_edits = {}  # key: property name, value: (QLineEdit for value, remove button)
        self.reserved_props = {"x", "y", "Position"}

        layout = QVBoxLayout()

        self.node_details_label = QLabel(f"Node ID: {node_data['id']}")
        layout.addWidget(self.node_details_label)

        self.position_label = QLabel(f"Position: {node_data['properties'].get('Position')}")
        layout.addWidget(self.position_label)

        # Editable label field
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Node Label")
        labels = node_data.get("labels", [])
        self.label_edit.setText(labels[0] if labels else "")
        layout.addWidget(QLabel("Label:"))
        layout.addWidget(self.label_edit)

        # Properties section
        layout.addWidget(QLabel("Properties:"))
        self.props_container = QVBoxLayout()
        self._populate_properties()
        layout.addLayout(self.props_container)

        # Add property controls
        add_prop_layout = QHBoxLayout()
        self.new_prop_name = QLineEdit()
        self.new_prop_name.setPlaceholderText("Property Name")
        self.new_prop_value = QLineEdit()
        self.new_prop_value.setPlaceholderText("Value")
        add_btn = QPushButton("Add Property")
        add_btn.clicked.connect(self.add_property)
        add_prop_layout.addWidget(self.new_prop_name)
        add_prop_layout.addWidget(self.new_prop_value)
        add_prop_layout.addWidget(add_btn)
        layout.addLayout(add_prop_layout)

        # Important checkbox
        self.important_checkbox = QCheckBox("Important node")
        self.important_checkbox.setChecked(bool(self.node_data["properties"].get("important", False)))
        layout.addWidget(self.important_checkbox)

        # Save and close buttons
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_label_and_properties)
        layout.addWidget(save_button)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def _populate_properties(self):
        # Clear previous widgets
        for i in reversed(range(self.props_container.count())):
            item = self.props_container.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.property_edits.clear()
        for key, value in self.node_data["properties"].items():
            if key in self.reserved_props:
                continue
            prop_layout = QHBoxLayout()
            name_label = QLabel(key)
            value_edit = QLineEdit(str(value))
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedWidth(60)
            remove_btn.clicked.connect(lambda _, k=key: self.remove_property(k))
            prop_layout.addWidget(name_label)
            prop_layout.addWidget(value_edit)
            prop_layout.addWidget(remove_btn)
            container = QWidget()
            container.setLayout(prop_layout)
            self.props_container.addWidget(container)
            self.property_edits[key] = (value_edit, remove_btn)

    def add_property(self):
        name = self.new_prop_name.text().strip()
        value = self.new_prop_value.text().strip()
        if not name or name in self.reserved_props or name in self.property_edits:
            QMessageBox.warning(self, "Invalid Property", "Property name is invalid or already exists.")
            return
        self.node_data["properties"][name] = value
        self._populate_properties()
        self.new_prop_name.clear()
        self.new_prop_value.clear()

    def remove_property(self, key):
        if key in self.node_data["properties"]:
            del self.node_data["properties"][key]
            self._populate_properties()

    def save_label_and_properties(self):
        new_label = self.label_edit.text().strip()
        if not new_label:
            QMessageBox.warning(self, "Invalid Label", "Label cannot be empty.")
            return
        try:
            # Update label
            if self.db_handler:
                self.db_handler.update_node_label(self.node_data["id"], new_label)
            # Update properties
            updated_props = {}
            for key in self.node_data["properties"]:
                if key in self.reserved_props:
                    updated_props[key] = self.node_data["properties"][key]
                elif key in self.property_edits:
                    updated_props[key] = self.property_edits[key][0].text()
            # Add new properties
            for key in self.property_edits:
                if key not in updated_props:
                    updated_props[key] = self.property_edits[key][0].text()
            # Save important flag
            updated_props["important"] = self.important_checkbox.isChecked()
            # Save to database
            if self.db_handler:
                self.db_handler.update_node_properties(self.node_data["id"], updated_props)
            QMessageBox.information(self, "Success", "Label and properties updated.")
            if self.refresh_callback:
                self.refresh_callback()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update: {e}")

# Window to display edge information
class EdgeInfoWindow(QDialog):
    def __init__(self, edge_data, start_node, end_node, db_handler=None, refresh_callback=None):
        super().__init__()
        self.setWindowTitle("Edge Details")
        self.setGeometry(200, 200, 400, 300)
        
        self.edge_data = edge_data
        self.start_node = start_node
        self.end_node = end_node
        self.db_handler = db_handler
        self.refresh_callback = refresh_callback
        
        layout = QVBoxLayout()
        
        # Display connected nodes info
        layout.addWidget(QLabel(f"From Node: {start_node['labels'][0] if start_node['labels'] else 'Node'} "
                              f"({start_node['properties'].get('Position')})"))
        layout.addWidget(QLabel(f"To Node: {end_node['labels'][0] if end_node['labels'] else 'Node'} "
                              f"({end_node['properties'].get('Position')})"))
        
        # Edge label edit
        layout.addWidget(QLabel("Edge Label:"))
        self.label_edit = QLineEdit()
        self.label_edit.setText(edge_data["properties"].get("label", ""))
        layout.addWidget(self.label_edit)
        
        # Edge weight edit
        layout.addWidget(QLabel("Edge Weight:"))
        self.weight_edit = QLineEdit()
        self.weight_edit.setText(str(edge_data["properties"].get("weight", 1.0)))
        layout.addWidget(self.weight_edit)
        
        # Properties section (similar to NodeInfoWindow)
        layout.addWidget(QLabel("Additional Properties:"))
        self.props_container = QVBoxLayout()
        self.property_edits = {}
        self.reserved_props = {"label", "weight"}
        self._populate_properties()
        layout.addLayout(self.props_container)
        
        # Add property controls
        add_prop_layout = QHBoxLayout()
        self.new_prop_name = QLineEdit()
        self.new_prop_name.setPlaceholderText("Property Name")
        self.new_prop_value = QLineEdit()
        self.new_prop_value.setPlaceholderText("Value")
        add_btn = QPushButton("Add Property")
        add_btn.clicked.connect(self.add_property)
        add_prop_layout.addWidget(self.new_prop_name)
        add_prop_layout.addWidget(self.new_prop_value)
        add_prop_layout.addWidget(add_btn)
        layout.addLayout(add_prop_layout)
        
        # Save and close buttons
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)
        
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def _populate_properties(self):
        for i in reversed(range(self.props_container.count())):
            item = self.props_container.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                
        self.property_edits.clear()
        for key, value in self.edge_data["properties"].items():
            if key in self.reserved_props:
                continue
            prop_layout = QHBoxLayout()
            name_label = QLabel(key)
            value_edit = QLineEdit(str(value))
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedWidth(60)
            remove_btn.clicked.connect(lambda _, k=key: self.remove_property(k))
            prop_layout.addWidget(name_label)
            prop_layout.addWidget(value_edit)
            prop_layout.addWidget(remove_btn)
            container = QWidget()
            container.setLayout(prop_layout)
            self.props_container.addWidget(container)
            self.property_edits[key] = (value_edit, remove_btn)
    
    def add_property(self):
        name = self.new_prop_name.text().strip()
        value = self.new_prop_value.text().strip()
        if not name or name in self.reserved_props or name in self.property_edits:
            QMessageBox.warning(self, "Invalid Property", "Property name is invalid or already exists.")
            return
        self.edge_data["properties"][name] = value
        self._populate_properties()
        self.new_prop_name.clear()
        self.new_prop_value.clear()
    
    def remove_property(self, key):
        if key in self.edge_data["properties"]:
            del self.edge_data["properties"][key]
            self._populate_properties()
    
    def save_changes(self):
        try:
            new_label = self.label_edit.text().strip()
            try:
                new_weight = float(self.weight_edit.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Weight", "Weight must be a number.")
                return
            
            # Update properties
            updated_props = {
                "label": new_label,
                "weight": new_weight
            }
            
            # Add other properties
            for key in self.property_edits:
                updated_props[key] = self.property_edits[key][0].text()
            
            # Save to database
            if self.db_handler:
                self.db_handler.update_edge_properties(
                    self.edge_data["identity"],
                    updated_props
                )
            
            if self.refresh_callback:
                self.refresh_callback()
            
            QMessageBox.information(self, "Success", "Edge properties updated successfully.")
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update edge: {e}")