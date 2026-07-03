from kg.neo4j_client import Neo4jClient


def build_graph(client: Neo4jClient) -> None:
    """Create constraints and indexes needed by the Knowledge Graph MVP."""
    statements = [
        """
        CREATE CONSTRAINT entity_uid_unique IF NOT EXISTS
        FOR (e:Entity)
        REQUIRE e.uid IS UNIQUE
        """,
        """
        CREATE INDEX entity_canonical_name IF NOT EXISTS
        FOR (e:Entity)
        ON (e.canonical_name)
        """,
        """
        CREATE INDEX entity_type IF NOT EXISTS
        FOR (e:Entity)
        ON (e.type)
        """,
        """
        CREATE INDEX entity_name IF NOT EXISTS
        FOR (e:Entity)
        ON (e.name)
        """,
    ]

    for statement in statements:
        client.write(statement)

