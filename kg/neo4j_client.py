import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase


class Neo4jClient:
    """Small wrapper around the official Neo4j driver."""

    def __init__(self) -> None:
        load_dotenv()
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        connection_timeout = float(os.getenv("NEO4J_CONNECTION_TIMEOUT", "1"))
        max_retry_time = float(os.getenv("NEO4J_MAX_RETRY_TIME", "1"))

        if not password:
            raise ValueError("NEO4J_PASSWORD is not set. Copy .env.example to .env and fill it.")

        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            connection_timeout=connection_timeout,
            max_transaction_retry_time=max_retry_time,
        )

    def write(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            result = session.execute_write(self._run, query, parameters or {})
            return result

    def read(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            result = session.execute_read(self._run, query, parameters or {})
            return result

    def close(self) -> None:
        self.driver.close()

    @staticmethod
    def _run(tx, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        result = tx.run(query, parameters)
        return [{key: record[key] for key in record.keys()} for record in result]
