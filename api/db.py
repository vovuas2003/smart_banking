import threading
from typing import Any, Dict, Iterable, Optional, Tuple, Union

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Допустимые значения изоляции, можно расширить
ISOLATION_MAP = {
    "autocommit": ISOLATION_LEVEL_AUTOCOMMIT,
    "read_committed": psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
    "repeatable_read": psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ,
    "serializable": psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE,
}

Params = Optional[Union[Dict[str, Any], Tuple[Any, ...]]]

class Database:
    _instance = None
    _lock = threading.RLock()
    _configured = False

    def __init__(self, dsn: str, minconn: int = 1, maxconn: int = 10):
        # не вызывать напрямую — пользуйся configure()/instance()
        self._pool = ThreadedConnectionPool(minconn, maxconn, dsn=dsn)

    @classmethod
    def configure(cls, dsn: str, minconn: int = 1, maxconn: int = 10):
        with cls._lock:
            cls._dsn = dsn
            cls._minconn = minconn
            cls._maxconn = maxconn
            cls._configured = True

    @classmethod
    def instance(cls) -> "Database":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if not cls._configured:
                        raise RuntimeError("Database is not configured")
                    cls._instance = Database(cls._dsn, cls._minconn, cls._maxconn)
        return cls._instance

    # --- приватные утилиты ---
    def _get_conn_cursor(self, isolation: str):
        conn = self._pool.getconn()
        prev_iso = conn.isolation_level
        conn.set_session(isolation_level=ISOLATION_MAP[isolation])
        return conn, conn.cursor(), prev_iso

    def _cleanup(self, conn, cur, prev_iso, success: bool):
        try:
            if success:
                if conn.isolation_level != ISOLATION_LEVEL_AUTOCOMMIT:
                    conn.commit()
            else:
                conn.rollback()
        finally:
            try:
                conn.set_session(isolation_level=prev_iso)
            except Exception:
                pass
            cur.close()
            self._pool.putconn(conn)

    # --- публичные методы JDBC-подобного стиля ---
    def execute(self, sql: str, isolation: str = "read_committed", params: Params = None) -> int:
        """
        Выполнить команду (INSERT/UPDATE/DELETE/DDL). Возвращает rowcount.
        """
        conn, cur, prev_iso = self._get_conn_cursor(isolation)
        ok = False
        try:
            cur.execute(sql, params)
            ok = True
            return cur.rowcount
        finally:
            self._cleanup(conn, cur, prev_iso, ok)

    def fetch_one(self, sql: str, isolation: str = "read_committed", params: Params = None):
        conn, cur, prev_iso = self._get_conn_cursor(isolation)
        ok = False
        try:
            cur.execute(sql, params)
            ok = True
            return cur.fetchone()
        finally:
            self._cleanup(conn, cur, prev_iso, ok)

    def fetch_all(self, sql: str, isolation: str = "read_committed", params: Params = None):
        conn, cur, prev_iso = self._get_conn_cursor(isolation)
        ok = False
        try:
            cur.execute(sql, params)
            ok = True
            return cur.fetchall()
        finally:
            self._cleanup(conn, cur, prev_iso, ok)

    def fetch_one_returning(self, sql: str, isolation: str = "read_committed", params: Params = None):
        """Удобно для INSERT ... RETURNING id"""
        return self.fetch_one(sql, isolation, params)

    # ping для healthcheck
    def ping(self):
        conn, cur, prev_iso = self._get_conn_cursor("autocommit")
        ok = False
        try:
            cur.execute("SELECT 1")
            cur.fetchone()
            ok = True
        finally:
            self._cleanup(conn, cur, prev_iso, ok)
