from database import Neo4jHandler as db
from utils import utils
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton  
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QPoint
import warnings
from editWindow import NodeInfoWindow, EdgeInfoWindow
import os
from dotenv import load_dotenv



clickNumber=2
edgeNode1=None
edgeNode2=None


warnings.filterwarnings("ignore", category=DeprecationWarning)

class NodeVisualizer(QMainWindow):
    
    
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self.node_positions = []
        self.edges = []
        self.delete_mode = False

        self.dragging_node = None  
        self.drag_offset = (0, 0)  

        self.setWindowTitle("Neo4j Node Visualizer")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: white")
        self.load_existing_nodes()
        self.load_existing_edges()

        #Organize Button
        self.organize_button = QPushButton("Organize Nodes", self)
        self.organize_button.setGeometry(20, 20, 140, 40)
        self.organize_button.clicked.connect(lambda: utils.organize_nodes(self))

    def load_existing_nodes(self):
        """
        Fetch all nodes from the database and add their positions to the visualization.
        """
        try:
            nodes = self.db_handler.get_all_nodes()
            for node in nodes:
                # Extract x and y from node properties
                x = node["properties"].get("x")
                y = node["properties"].get("y")
                if x is not None and y is not None:
                    self.node_positions.append((x, y))

            print(f"Loaded {len(self.node_positions)} nodes from the database.")

        except Exception as e:
            print(f"Error loading nodes: {e}")

    def load_existing_edges(self):
        """
        Fetch all edges from the database and add them to the local storage.
        """
        try:
            edges = self.db_handler.get_all_edges()  # Fetch edges
            for edge in edges:
                node1_id = edge["start"]
                node2_id = edge["end"]

                # Fetch full node details using their IDs
                node1 = self.db_handler.get_node_by_id(node1_id)
                node2 = self.db_handler.get_node_by_id(node2_id)

                # Ensure nodes are valid before adding
                if node1 and node2:
                    #print(node1, node2)
                    self.edges.append({
                        "start": node1,
                        "end": node2,
                        "properties": edge.get("properties", {})
                    })

            print(f"Loaded {len(self.edges)} edges from the database.")

        except Exception as e:
            print(f"Error loading edges: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.delete_mode = not self.delete_mode
            if self.delete_mode:
                self.setWindowTitle("Neo4j Node Visualizer [DELETE MODE]")
            else:
                self.setWindowTitle("Neo4j Node Visualizer")
            self.update()

    def mousePressEvent(self, event):
        global clickNumber, edgeNode1, edgeNode2
        x, y = event.x(), event.y()

        # --- Node dragging logic ---
        if event.button() == Qt.LeftButton and not self.delete_mode:
            # Check if a node is under the cursor
            for node in self.db_handler.get_all_nodes():
                nx = node["properties"].get("x")
                ny = node["properties"].get("y")
                if nx is not None and ny is not None:
                    if utils.getDistance(x, y, nx, ny) <= 20:
                        self.dragging_node = node
                        self.drag_offset = (nx - x, ny - y)
                        return  # Don't add a new node if dragging
        if self.delete_mode and event.button() == Qt.LeftButton:
            # Delete node mode
            try:
                closestNode = utils.getClosestNode(self, x, y)
            except Exception as e:
                print(f"Error finding closest node: {e}")
                return
            if utils.getDistance(x, y, closestNode["properties"].get("x"), closestNode["properties"].get("y")) <= 20:
                node_id = closestNode["id"]
                try:
                    self.db_handler.delete_node_and_edges(node_id)
                    # Remove node from local lists
                    self.node_positions = [
                        (nx, ny)
                        for (nx, ny) in self.node_positions
                        if not (nx == closestNode["properties"].get("x") and ny == closestNode["properties"].get("y"))
                    ]
                    self.edges = [
                        edge
                        for edge in self.edges
                        if edge["start"]["id"] != node_id and edge["end"]["id"] != node_id
                    ]
                    print(f"Deleted node {node_id} and its edges.")
                    self.update()
                except Exception as e:
                    print(f"Error deleting node: {e}")
            return

        if event.button() == Qt.LeftButton:
            # Left button clicked - Add a new node
            self.node_positions.append((x, y))

            # Add a node to the Neo4j database
            try:
                self.db_handler.add_node("Point", {"Position": f"{x}:{y}", "x": x, "y": y})
                print(f"Node added at ({x}, {y})")
            except Exception as e:
                print(f"Error adding node: {e}")

            # Trigger a repaint to draw the circle
            self.update()

        elif event.button() == Qt.RightButton:
            # Right button clicked - Create an edge

            if clickNumber == 2:
                edgeNode1 = None
                closestNode = utils.getClosestNode(self, x, y)
                if utils.getDistance(x, y, closestNode["properties"].get("x"), closestNode["properties"].get("y")) <= 20:
                    edgeNode1 = closestNode
                    clickNumber = 1

            elif clickNumber == 1:
                edgeNode2 = None
                closestNode = utils.getClosestNode(self, x, y)
                if utils.getDistance(x, y, closestNode["properties"].get("x"), closestNode["properties"].get("y")) <= 20:
                    edgeNode2 = closestNode
                    clickNumber = 2

            if edgeNode1 and edgeNode2 and edgeNode1 != edgeNode2:
                id1 = edgeNode1["id"]
                id2 = edgeNode2["id"]
                # Add default properties with label
                edge_props = {
                    "weight": 1.5,
                    "label": "CONNECTED"  # Default label
                }
                db.add_edge(self.db_handler, id1, id2, "CONNECTED", edge_props)
                # Store the edge locally with properties
                self.edges.append({
                    "start": edgeNode1,
                    "end": edgeNode2,
                    "properties": edge_props
                })
                edgeNode1 = None
                edgeNode2 = None
                self.update()

        elif event.button() == Qt.MiddleButton:
            # Middle button clicked - Open Node Info Window or Edge Info Window
            closest_node = utils.getClosestNode(self, x, y)
            if utils.getDistance(x, y, closest_node["properties"].get("x"), closest_node["properties"].get("y")) <= 20:
                if closest_node:
                    # Open the node info window, pass db_handler and refresh callback
                    node_info_window = NodeInfoWindow(
                        closest_node,
                        db_handler=self.db_handler,
                        refresh_callback=self.refresh_nodes_and_edges
                    )
                    node_info_window.exec_()
            else:
                # If no close node found, try to find a close edge
                closest_edge = utils.getClosestEdge(self, x, y)
                if closest_edge:
                    edge_info_window = EdgeInfoWindow(
                        closest_edge["edge"],
                        closest_edge["start_node"],
                        closest_edge["end_node"],
                        db_handler=self.db_handler,
                        refresh_callback=self.refresh_nodes_and_edges
                    )
                    edge_info_window.exec_()

    def mouseMoveEvent(self, event):
        if self.dragging_node:
            x, y = event.x(), event.y()
            new_x = x + self.drag_offset[0]
            new_y = y + self.drag_offset[1]
            # Update locally
            self.dragging_node["properties"]["x"] = new_x
            self.dragging_node["properties"]["y"] = new_y
            # Update in database
            node_id = self.dragging_node["id"]
            properties = self.dragging_node["properties"].copy()
            properties["Position"] = f"{new_x}:{new_y}"
            self.db_handler.update_node_properties(node_id, properties)
            self.refresh_nodes_and_edges()  # Reload positions and redraw

    def mouseReleaseEvent(self, event):
        if self.dragging_node:
            self.dragging_node = None

    def refresh_nodes_and_edges(self):
        self.node_positions.clear()
        self.edges.clear()
        self.load_existing_nodes()
        self.load_existing_edges()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Count total edges between each unordered node pair (ignoring direction)
        unordered_edge_counts = {}  # frozenset({id1, id2}) -> total edges (both directions)
        for edge in self.edges:
            node1_id, node2_id = edge["start"]["id"], edge["end"]["id"]
            node_pair = frozenset([node1_id, node2_id])
            unordered_edge_counts[node_pair] = unordered_edge_counts.get(node_pair, 0) + 1

        # Track index of each edge (per direction) for offset
        edge_index_map = {}

        # Draw edges
        for edge in self.edges:
            node1, node2 = edge["start"], edge["end"]
            if node1 and node2 and "properties" in node1 and "properties" in node2:
                x1, y1 = node1["properties"].get("x"), node1["properties"].get("y")
                x2, y2 = node2["properties"].get("x"), node2["properties"].get("y")

                if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                    # Use direction for edge_index, but unordered for total_edges
                    node_pair_dir = (node1["id"], node2["id"])
                    node_pair_unordered = frozenset([node1["id"], node2["id"]])
                    edge_index = edge_index_map.get(node_pair_dir, 0)
                    total_edges = unordered_edge_counts[node_pair_unordered]

                    # Get edge label from properties
                    edge_label = edge.get("properties", {}).get("label", "")
                    utils.draw_arrow(painter, x1, y1, x2, y2, edge_index, total_edges, edge_label)

                    edge_index_map[node_pair_dir] = edge_index + 1

        # Draw nodes and their labels
        for node in self.db_handler.get_all_nodes():
            x = node["properties"].get("x")
            y = node["properties"].get("y")
            if x is not None and y is not None:
                # Check if node is important
                if node["properties"].get("important", False):
                    painter.setBrush(QColor(255, 200, 0))  # Gold/Yellow for important
                else:
                    painter.setBrush(QColor(0, 150, 255))  # Default blue
                painter.drawEllipse(QPoint(x, y), 20, 20)
                labels = node.get("labels", [])
                label = labels[0] if labels else f"{x}:{y}"
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(x - 15, y + 5, label)

        # Draw delete mode indicator in the top right corner
        indicator_margin = 20
        indicator_width = 120
        indicator_height = 60  
        rect_x = self.width() - indicator_width - indicator_margin
        rect_y = indicator_margin

        if self.delete_mode:
            painter.setBrush(QColor(255, 80, 80, 200))
            painter.setPen(QColor(180, 0, 0))
            text_main = "DELETE MODE: ON"
        else:
            painter.setBrush(QColor(200, 200, 200, 180))
            painter.setPen(QColor(80, 80, 80))
            text_main = "DELETE MODE: OFF"

        text_hint = "(Press R to toggle)"

        painter.drawRect(rect_x, rect_y, indicator_width, indicator_height)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(rect_x + 12, rect_y + 24, text_main)
        painter.drawText(rect_x + 12, rect_y + 44, text_hint)

        painter.end()




if __name__ == "__main__":
    load_dotenv()
    
    uri=os.getenv('URI')
    user=os.getenv('USER')
    password=os.getenv('PASSWORD')
    

    # Initialize the handler
    db_handler = db(uri, user, password)

    # Start the PyQt5 application
    app = QApplication(sys.argv)
    window = NodeVisualizer(db_handler)
    window.show()

    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        # Close the Neo4j connection when the app exits
        db_handler.close()
