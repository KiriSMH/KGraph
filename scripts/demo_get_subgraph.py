import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kg.neo4j_client import Neo4jClient
from kg.queries import get_subgraph


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a JSON-compatible subgraph around an entity.")
    parser.add_argument("entity_name", help="Entity name or alias, for example: вещество Б")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    client = Neo4jClient()
    try:
        subgraph = get_subgraph(client, args.entity_name, depth=args.depth, limit=args.limit)
        print(json.dumps(subgraph, ensure_ascii=False, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
