from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kg.neo4j_client import Neo4jClient
from kg.schema import build_graph


def main() -> None:
    client = Neo4jClient()
    try:
        build_graph(client)
        print("Neo4j schema is ready.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
