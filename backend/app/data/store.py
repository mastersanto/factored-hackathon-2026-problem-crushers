"""Read-only access to the Parquet warehouse through DuckDB."""
from __future__ import annotations

import threading
from datetime import datetime
from functools import lru_cache

import duckdb

from app.config import settings

from app.data.build import TABLES  # noqa: E402  (single source of the table list)


class Store:
    def __init__(self, warehouse_dir=settings.warehouse_dir):
        missing = [t for t in TABLES if not (warehouse_dir / f"{t}.parquet").exists()]
        if missing:
            raise RuntimeError(f"Warehouse incomplete ({', '.join(missing)}): run `python -m app.data.build` first")
        self._con = duckdb.connect()
        for t in TABLES:
            self._con.sql(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{warehouse_dir / t}.parquet')")
        self._lock = threading.Lock()
        # The dataset ends in June 2026; "now" for the assistant is the last recorded transaction.
        self.as_of: datetime = self.query_one("SELECT max(transaction_date) FROM transactions")[0]

    def query(self, sql: str, params: list | None = None) -> list[dict]:
        with self._lock:
            cur = self._con.cursor()
            rel = cur.execute(sql, params or [])
            cols = [d[0] for d in rel.description]
            return [dict(zip(cols, row)) for row in rel.fetchall()]

    def query_one(self, sql: str, params: list | None = None):
        with self._lock:
            return self._con.cursor().execute(sql, params or []).fetchone()


@lru_cache(maxsize=1)
def get_store() -> Store:
    return Store()
