import math
from database import Neo4jHandler as db
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtCore import QPoint

from PyQt5.QtGui import QPainterPath
from PyQt5.QtCore import Qt
import math


class utils:
    def getDistance(x1, y1, x2, y2):
        #print("tavolsagok")
        #print(math.sqrt((x2-x1)**2+(y2-y1)**2))
        return math.sqrt((x2-x1)**2+(y2-y1)**2)
        
    
    def getClosestNode(self, x, y):
        nodes = db.get_all_nodes(self.db_handler)

        minDistance=-1

        for node in nodes:
            
            
            node_x = int(node["properties"].get("x"))
            node_y = int(node["properties"].get("y"))
            distance = utils.getDistance(x, y, node_x, node_y)
            if minDistance==-1 or distance<minDistance:
                minDistance=distance
                minNode=node
        #print(minDistance)
        #print(minNode)
        return minNode
    
    def getClosestEdge(self, x, y):
        """Find the closest edge label to a point (x,y)"""
        edges = self.db_handler.get_all_edges()
        min_distance = float('inf')
        closest_edge = None
        
        # Count edges between each pair of nodes (similar to paintEvent logic)
        unordered_edge_counts = {}  # frozenset({id1, id2}) -> total edges
        edge_index_map = {}  # (id1, id2) -> current index
        
        for edge in edges:
            node1_id, node2_id = edge["start"], edge["end"]
            node_pair_unordered = frozenset([node1_id, node2_id])
            unordered_edge_counts[node_pair_unordered] = unordered_edge_counts.get(node_pair_unordered, 0) + 1
        
        for edge in edges:
            # Get the start and end nodes
            start_node = self.db_handler.get_node_by_id(edge["start"])
            end_node = self.db_handler.get_node_by_id(edge["end"])
            
            if start_node and end_node:
                x1 = start_node["properties"].get("x")
                y1 = start_node["properties"].get("y")
                x2 = end_node["properties"].get("x")
                y2 = end_node["properties"].get("y")
                
                if x1 and y1 and x2 and y2:
                    # Get edge index and total edges (similar to paintEvent logic)
                    node_pair_dir = (edge["start"], edge["end"])
                    node_pair_unordered = frozenset([edge["start"], edge["end"]])
                    edge_index = edge_index_map.get(node_pair_dir, 0)
                    total_edges = unordered_edge_counts[node_pair_unordered]
                    
                    # Calculate offset (same as in draw_arrow)
                    max_offset = 200
                    step = max_offset / (total_edges - 1) if total_edges > 1 else 0
                    offset = (edge_index - (total_edges - 1) / 2) * step
                    
                    # Update edge index for this direction
                    edge_index_map[node_pair_dir] = edge_index + 1
                    
                    # Calculate the control point (needed for quadratic Bézier curve)
                    angle = math.atan2(y2 - y1, x2 - x1)
                    perp_x = math.cos(angle + math.pi / 2)
                    perp_y = math.sin(angle + math.pi / 2)
                    
                    # Calculate midpoint
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    
                    # Calculate control point with offset
                    control_x = mid_x + offset * perp_x
                    control_y = mid_y + offset * perp_y
                    
                    # Calculate label position (t=0.5 on the Bézier curve)
                    t = 0.5
                    label_x = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * control_x + t ** 2 * x2
                    label_y = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * control_y + t ** 2 * y2
                    
                    # Calculate distance to label position
                    distance = math.sqrt((x - label_x)**2 + (y - label_y)**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_edge = {
                            "edge": edge,
                            "start_node": start_node,
                            "end_node": end_node
                        }
        
        return closest_edge if min_distance <= 30 else None  

    def draw_arrow(painter, start_x, start_y, end_x, end_y, edge_index=0, total_edges=1, label=""):
        arrow_size = 10
        
        max_offset = 200 
        offset = 0

        angle = math.atan2(end_y - start_y, end_x - start_x)
        perp_x = math.cos(angle + math.pi / 2)
        perp_y = math.sin(angle + math.pi / 2)

        # Even spacing around center
        if total_edges > 1:
            step = max_offset / (total_edges - 1)  
            offset = (edge_index - (total_edges - 1) / 2) * step

        # Midpoint and control point for Bézier
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        control_x = mid_x + offset * perp_x
        control_y = mid_y + offset * perp_y

        # Draw curve
        path = QPainterPath()
        path.moveTo(start_x, start_y)
        path.quadTo(control_x, control_y, end_x, end_y)
        painter.setPen(QColor(255, 0, 0))
        painter.drawPath(path)

        # Compute arrowhead position and orientation using Bézier derivative
        t = 0.9
        # Bézier curve point
        arrow_x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * end_x
        arrow_y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * end_y
        # Derivative for tangent
        dx = 2 * (1 - t) * (control_x - start_x) + 2 * t * (end_x - control_x)
        dy = 2 * (1 - t) * (control_y - start_y) + 2 * t * (end_y - control_y)
        angle = math.atan2(dy, dx)

        # Arrowhead points
        arrow_p1 = QPoint(int(arrow_x - arrow_size * math.cos(angle + math.pi / 6)),
                          int(arrow_y - arrow_size * math.sin(angle + math.pi / 6)))
        arrow_p2 = QPoint(int(arrow_x - arrow_size * math.cos(angle - math.pi / 6)),
                          int(arrow_y - arrow_size * math.sin(angle - math.pi / 6)))

        painter.drawLine(QPoint(int(arrow_x), int(arrow_y)), arrow_p1)
        painter.drawLine(QPoint(int(arrow_x), int(arrow_y)), arrow_p2)
        
        # Add label drawing at a point along the curve
        if label:
            painter.save()
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            
            # Calculate label position at t=0.5 (middle of the curve)
            t = 0.5
            label_x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * end_x
            label_y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * end_y
            
            # Draw white background for better readability
            text_rect = painter.fontMetrics().boundingRect(label)
            text_rect.moveCenter(QPoint(int(label_x), int(label_y)))
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect.adjusted(-3, -3, 3, 3))
            
            # Draw text
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(QPoint(int(label_x - text_rect.width()/2), 
                                  int(label_y + text_rect.height()/2)), 
                            label)
            painter.restore()
            
    def organize_nodes(visualizer):
        """
        Arrange important nodes in the center and others in a circle around them.
        Updates positions locally and in the database.
        """
        nodes = visualizer.db_handler.get_all_nodes()
        if not nodes:
            return

        # Separate important and non-important nodes
        important_nodes = [n for n in nodes if n["properties"].get("important", False)]
        other_nodes = [n for n in nodes if not n["properties"].get("important", False)]

        center_x, center_y = visualizer.width() // 2, visualizer.height() // 2

        # Place important nodes in the center (clustered if multiple)
        if important_nodes:
            imp_radius = 60  
            for i, node in enumerate(important_nodes):
                angle = 2 * math.pi * i / max(1, len(important_nodes))
                x = int(center_x + imp_radius * math.cos(angle))
                y = int(center_y + imp_radius * math.sin(angle))
                node["properties"]["x"] = x
                node["properties"]["y"] = y
                node["properties"]["Position"] = f"{x}:{y}"
                visualizer.db_handler.update_node_properties(node["id"], node["properties"])

        # Arrange other nodes in a circle around the center
        n = len(other_nodes)
        if n > 0:
            radius = min(visualizer.width(), visualizer.height()) // 2 - 80
            for i, node in enumerate(other_nodes):
                angle = 2 * math.pi * i / n
                x = int(center_x + radius * math.cos(angle))
                y = int(center_y + radius * math.sin(angle))
                node["properties"]["x"] = x
                node["properties"]["y"] = y
                node["properties"]["Position"] = f"{x}:{y}"
                visualizer.db_handler.update_node_properties(node["id"], node["properties"])

        visualizer.refresh_nodes_and_edges()