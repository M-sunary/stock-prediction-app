"""
本地缓存管理器 - SQLite + Pickle
避免频繁请求外部 API
"""
import os
import json
import pickle
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'cache'
)


class CacheManager:
    def __init__(self):
        os.makedirs(_CACHE_DIR, exist_ok=True)
        self._db_path = os.path.join(_CACHE_DIR, 'cache.db')
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kv_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prediction_history (
                    code TEXT,
                    date TEXT,
                    probability REAL,
                    direction TEXT,
                    actual_result TEXT,
                    actual_pct REAL,
                    correct INTEGER,
                    PRIMARY KEY (code, date)
                )
            """)
            conn.commit()

    # ── KV 缓存（JSON 序列化）───────────────────────────────────────────────
    def get(self, key: str, max_age_hours: float = 1.0) -> Optional[dict]:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT value, updated_at FROM kv_cache WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return None
        value, updated_at = row
        age = datetime.now() - datetime.fromisoformat(updated_at)
        if age.total_seconds() / 3600 > max_age_hours:
            return None
        return json.loads(value)

    def set(self, key: str, value: dict):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv_cache(key, value, updated_at) VALUES(?,?,?)",
                (key, json.dumps(value, default=str), datetime.now().isoformat())
            )
            conn.commit()

    # ── DataFrame 缓存（Pickle）─────────────────────────────────────────────
    def get_df(self, key: str, max_age_hours: float = 4.0) -> Optional[pd.DataFrame]:
        path = os.path.join(_CACHE_DIR, f"{key}.pkl")
        if not os.path.exists(path):
            return None
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        age = datetime.now() - mtime
        if age.total_seconds() / 3600 > max_age_hours:
            return None
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None

    def set_df(self, key: str, df: pd.DataFrame):
        path = os.path.join(_CACHE_DIR, f"{key}.pkl")
        with open(path, 'wb') as f:
            pickle.dump(df, f)

    # ── 预测历史 ─────────────────────────────────────────────────────────────
    def save_prediction(self, code: str, date: str, probability: float,
                        direction: str, actual_result: str = None,
                        actual_pct: float = None, correct: bool = None):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO prediction_history
                   (code, date, probability, direction, actual_result, actual_pct, correct)
                   VALUES(?,?,?,?,?,?,?)""",
                (code, date, probability, direction, actual_result, actual_pct,
                 1 if correct else (0 if correct is not None else None))
            )
            conn.commit()

    def get_prediction_history(self, code: str, limit: int = 30) -> list:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """SELECT date, probability, direction, actual_result, actual_pct, correct
                   FROM prediction_history WHERE code=?
                   ORDER BY date DESC LIMIT ?""",
                (code, limit)
            ).fetchall()
        return [
            {
                'date': r[0], 'probability': r[1], 'direction': r[2],
                'actual_result': r[3], 'actual_pct': r[4],
                'correct': bool(r[5]) if r[5] is not None else None
            }
            for r in rows
        ]

    def get_accuracy_stats(self, code: str, days: int = 30) -> dict:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """SELECT correct FROM prediction_history
                   WHERE code=? AND correct IS NOT NULL
                   ORDER BY date DESC LIMIT ?""",
                (code, days)
            ).fetchall()
        if not rows:
            return {'wins': 0, 'losses': 0, 'accuracy': 0.0}
        wins = sum(1 for r in rows if r[0] == 1)
        losses = len(rows) - wins
        return {
            'wins': wins,
            'losses': losses,
            'accuracy': wins / len(rows) if rows else 0.0
        }


_instance = None

def get_cache() -> CacheManager:
    global _instance
    if _instance is None:
        _instance = CacheManager()
    return _instance
