import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kg.importer import import_json_file
from kg.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Knowledge Graph JSON into Neo4j.")
    parser.add_argument("json_path", help="Path to JSON file.")
    args = parser.parse_args()

    client = Neo4jClient()
    try:
        stats = import_json_file(client, args.json_path)
        print("Import completed.")
        for key, value in stats.items():
            print(f"{key}: {value}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
