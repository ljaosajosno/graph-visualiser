from neo4j import GraphDatabase




class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password), notifications_min_severity='OFF')

    def close(self):
        self.driver.close()

    def get_all_nodes(self):
            """
            Retrieve all nodes from the Neo4j database.

            Returns:
                list: A list of dictionaries containing node labels and properties.
            """
            query = "MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS properties"
            with self.driver.session() as session:
                result = session.run(query)
                nodes = [{"id": record["id"], "labels": record["labels"], "properties": record["properties"]} for record in result]
            return nodes
    
    def get_all_edges(self):
        """
        Retrieve all edges from the Neo4j database.


        Returns:
            list: A list of dictionaries containing edge relationships and properties.
        """
        
        query = "MATCH ()-[r]->() RETURN r"

        with self.driver.session() as session:
            result = session.run(query)
            edges = [
                {
                    "identity": record["r"].id,
                    "start": record["r"].start_node.id,
                    "end": record["r"].end_node.id,
                    "type": record["r"].type,
                    "properties": dict(record["r"].items())
                }
                for record in result
            ]

        self.driver.close()
        return edges

    def add_node(self, label, properties):
        """
        Adds a new node to the Neo4j database.

        :param label: The label of the node (e.g., "Person").
        :param properties: A dictionary of properties for the node (e.g., {"name": "Alice", "age": 30}).
        """
        with self.driver.session() as session:
            session.write_transaction(self._create_node, label, properties)

    def add_edge(self, node1_id, node2_id, relationship_type, relationship_properties=None):
        """
        Adds a relationship (edge) between two nodes in the Neo4j database.

        :param node1_id: The ID of the first node.
        :param node2_id: The ID of the second node.
        :param relationship_type: The type of the relationship (e.g., "FRIENDS").
        :param relationship_properties: Optional properties for the relationship including label.
        """
        if relationship_properties is None:
            relationship_properties = {}
        if 'label' not in relationship_properties:
            relationship_properties['label'] = relationship_type
        
        with self.driver.session() as session:
            session.write_transaction(
                self._create_relationship,
                node1_id,
                node2_id,
                relationship_type,
                relationship_properties
            )

    def get_node_by_id(self, node_id):
        query = "MATCH (n) WHERE id(n) = $node_id RETURN n"
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            if record:
                node = record["n"]
                return {
                    "id": node.id, 
                    "labels": list(node.labels),
                    "properties": dict(node._properties)
                }
            return None

    def delete_node_and_edges(self, node_id):
        """
        Deletes a node and all its connected edges from the Neo4j database.

        :param node_id: The ID of the node to delete.
        """
        with self.driver.session() as session:
            session.write_transaction(self._delete_node_and_edges, node_id)

    def update_node_label(self, node_id, new_label):
        """
        Updates the label of a node in the Neo4j database.
        :param node_id: The ID of the node to update.
        :param new_label: The new label to set.
        """
        with self.driver.session() as session:
            session.write_transaction(self._set_node_label, node_id, new_label)
    
    def update_node_properties(self, node_id, properties):
        with self.driver.session() as session:
            session.write_transaction(self._set_node_properties, node_id, properties)
    
    def update_edge_properties(self, edge_id, properties):
        """
        Updates the properties of an edge in the Neo4j database.
        
        :param edge_id: The ID of the edge to update
        :param properties: Dictionary of properties to set
        """
        with self.driver.session() as session:
            session.write_transaction(self._set_edge_properties, edge_id, properties)
    
    @staticmethod
    def _set_node_properties(tx, node_id, properties):
        query = "MATCH (n) WHERE id(n) = $node_id SET n = $properties RETURN n"
        tx.run(query, node_id=node_id, properties=properties)

    @staticmethod
    def _create_node(tx, label, properties):
        # Construct a Cypher query with dynamic labels and properties
        query = (
            f"CREATE (n:{label} $properties) "
            "RETURN n"
        )
        tx.run(query, properties=properties)

    @staticmethod
    def _create_relationship(tx, node1_id, node2_id, relationship_type, relationship_properties):
        query = (
            f"MATCH (a), (b) "
            "WHERE id(a) = $node1_id AND id(b) = $node2_id "
            f"CREATE (a)-[r:{relationship_type} $properties]->(b) "
            "RETURN a, b, r"
        )
        tx.run(query, node1_id=node1_id, node2_id=node2_id, properties=relationship_properties or {})

    @staticmethod
    def _delete_node_and_edges(tx, node_id):
        query = (
            "MATCH (n) WHERE id(n) = $node_id "
            "OPTIONAL MATCH (n)-[r]-() "
            "DELETE r, n"
        )
        tx.run(query, node_id=node_id)

    @staticmethod
    def _set_node_label(tx, node_id, new_label):
        # Remove all labels and set the new one
        query = (
            "MATCH (n) WHERE id(n) = $node_id "
            "REMOVE n:" + ":".join(["`" + l + "`" for l in tx.run("MATCH (n) WHERE id(n) = $node_id RETURN labels(n) AS labels", node_id=node_id).single()['labels']]) + " "
            "SET n:`" + new_label.replace('`', '') + "` "
            "RETURN n"
        )
        tx.run(query, node_id=node_id)

    @staticmethod
    def _set_edge_properties(tx, edge_id, properties):
        query = (
            "MATCH ()-[r]->() "
            "WHERE id(r) = $edge_id "
            "SET r = $properties "
            "RETURN r"
        )
        tx.run(query, edge_id=edge_id, properties=properties)



