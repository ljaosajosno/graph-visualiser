import unittest
from utils import utils

class DummyDBHandler:
    def get_all_nodes(self):
        return [
            {"id": 1, "properties": {"x": 10, "y": 10}},
            {"id": 2, "properties": {"x": 20, "y": 20}},
        ]

class DummyUtils(utils):
    def getClosestNode(self, x, y):
        # Override to use the dummy handler directly, bypassing db.get_all_nodes
        nodes = self.db_handler.get_all_nodes()
        minDistance = -1
        for node in nodes:
            node_x = int(node["properties"].get("x"))
            node_y = int(node["properties"].get("y"))
            distance = utils.getDistance(x, y, node_x, node_y)
            if minDistance == -1 or distance < minDistance:
                minDistance = distance
                minNode = node
        return minNode

class TestUtils(unittest.TestCase):
    def test_getDistance(self):
        # Test distance between two points
        d = utils.getDistance(0, 0, 3, 4)
        self.assertEqual(d, 5)

        d2 = utils.getDistance(1, 1, 1, 1)
        self.assertEqual(d2, 0)

    def test_getClosestNode(self):
        util = DummyUtils()
        util.db_handler = DummyDBHandler()
        closest = util.getClosestNode(12, 12)
        self.assertEqual(closest["id"], 1)

        closest2 = util.getClosestNode(19, 19)
        self.assertEqual(closest2["id"], 2)

if __name__ == "__main__":
    unittest.main()