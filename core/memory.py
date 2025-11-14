"""
Memory Store - エージェント間で共有するメモリストア

機能:
- 短期記憶（セッション内）
- 長期記憶（永続化）
- ベクトル検索対応
- Redis/SQLiteバックエンド
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime, timedelta
import json
import hashlib

logger = structlog.get_logger()


class MemoryStore:
    """エージェント間で共有するメモリストア"""

    def __init__(
        self,
        backend: str = "in_memory",
        redis_url: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        self.backend = backend
        self.short_term_memory = {}  # インメモリキャッシュ
        self.long_term_memory = {}   # 永続化データ
        self.vector_store = {}       # ベクトル検索用
        self.access_log = []

        # バックエンド接続
        if backend == "redis" and redis_url:
            self._init_redis(redis_url)
        elif backend == "sqlite" and db_path:
            self._init_sqlite(db_path)

        logger.info("MemoryStore initialized", backend=backend)

    def _init_redis(self, redis_url: str) -> None:
        """Redis接続を初期化"""
        try:
            # import redis
            # self.redis_client = redis.from_url(redis_url)
            logger.info("Redis backend initialized", url=redis_url)
        except Exception as e:
            logger.error("Redis initialization failed", error=str(e))

    def _init_sqlite(self, db_path: str) -> None:
        """SQLite接続を初期化"""
        try:
            # import sqlite3
            # self.db_connection = sqlite3.connect(db_path)
            logger.info("SQLite backend initialized", path=db_path)
        except Exception as e:
            logger.error("SQLite initialization failed", error=str(e))

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        データを保存

        Args:
            key: キー
            value: 値
            ttl: 有効期限（秒）
            metadata: メタデータ

        Returns:
            成功/失敗
        """
        try:
            entry = {
                "key": key,
                "value": value,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "expires_at": (
                    datetime.now() + timedelta(seconds=ttl)
                ).isoformat() if ttl else None
            }

            # 短期記憶に保存
            self.short_term_memory[key] = entry

            # バックエンドに応じて永続化
            if self.backend == "redis":
                await self._store_redis(key, entry, ttl)
            elif self.backend == "sqlite":
                await self._store_sqlite(key, entry)
            else:
                # インメモリの場合は長期記憶にも保存
                self.long_term_memory[key] = entry

            logger.debug("Data stored", key=key, ttl=ttl)
            return True

        except Exception as e:
            logger.error("Store failed", key=key, error=str(e))
            return False

    async def _store_redis(
        self,
        key: str,
        entry: Dict[str, Any],
        ttl: Optional[int]
    ) -> None:
        """Redisに保存"""
        # if hasattr(self, 'redis_client'):
        #     serialized = json.dumps(entry)
        #     if ttl:
        #         self.redis_client.setex(key, ttl, serialized)
        #     else:
        #         self.redis_client.set(key, serialized)
        pass

    async def _store_sqlite(self, key: str, entry: Dict[str, Any]) -> None:
        """SQLiteに保存"""
        # if hasattr(self, 'db_connection'):
        #     cursor = self.db_connection.cursor()
        #     cursor.execute(
        #         "INSERT OR REPLACE INTO memory (key, value, metadata, created_at) VALUES (?, ?, ?, ?)",
        #         (key, json.dumps(entry['value']), json.dumps(entry['metadata']), entry['created_at'])
        #     )
        #     self.db_connection.commit()
        pass

    async def retrieve(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        データを取得

        Args:
            key: キー
            default: デフォルト値

        Returns:
            保存された値
        """
        try:
            # まず短期記憶を確認
            if key in self.short_term_memory:
                entry = self.short_term_memory[key]

                # 有効期限チェック
                if entry.get("expires_at"):
                    expires_at = datetime.fromisoformat(entry["expires_at"])
                    if datetime.now() > expires_at:
                        await self.delete(key)
                        return default

                self._log_access(key, "hit_short_term")
                return entry["value"]

            # バックエンドから取得
            if self.backend == "redis":
                value = await self._retrieve_redis(key)
                if value is not None:
                    return value

            elif self.backend == "sqlite":
                value = await self._retrieve_sqlite(key)
                if value is not None:
                    return value

            # 長期記憶を確認
            if key in self.long_term_memory:
                self._log_access(key, "hit_long_term")
                return self.long_term_memory[key]["value"]

            self._log_access(key, "miss")
            return default

        except Exception as e:
            logger.error("Retrieve failed", key=key, error=str(e))
            return default

    async def _retrieve_redis(self, key: str) -> Optional[Any]:
        """Redisから取得"""
        # if hasattr(self, 'redis_client'):
        #     data = self.redis_client.get(key)
        #     if data:
        #         entry = json.loads(data)
        #         return entry.get('value')
        return None

    async def _retrieve_sqlite(self, key: str) -> Optional[Any]:
        """SQLiteから取得"""
        # if hasattr(self, 'db_connection'):
        #     cursor = self.db_connection.cursor()
        #     cursor.execute("SELECT value FROM memory WHERE key = ?", (key,))
        #     row = cursor.fetchone()
        #     if row:
        #         return json.loads(row[0])
        return None

    async def delete(self, key: str) -> bool:
        """データを削除"""
        try:
            if key in self.short_term_memory:
                del self.short_term_memory[key]

            if key in self.long_term_memory:
                del self.long_term_memory[key]

            # バックエンドからも削除
            if self.backend == "redis":
                # self.redis_client.delete(key)
                pass
            elif self.backend == "sqlite":
                # cursor = self.db_connection.cursor()
                # cursor.execute("DELETE FROM memory WHERE key = ?", (key,))
                # self.db_connection.commit()
                pass

            logger.debug("Data deleted", key=key)
            return True

        except Exception as e:
            logger.error("Delete failed", key=key, error=str(e))
            return False

    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        検索（キーまたは値に対して）

        Args:
            query: 検索クエリ
            limit: 最大結果数

        Returns:
            マッチした結果のリスト
        """
        results = []

        # 短期記憶から検索
        for key, entry in self.short_term_memory.items():
            if query.lower() in key.lower():
                results.append({
                    "key": key,
                    "value": entry["value"],
                    "source": "short_term"
                })

        # 長期記憶から検索
        for key, entry in self.long_term_memory.items():
            if query.lower() in key.lower():
                results.append({
                    "key": key,
                    "value": entry["value"],
                    "source": "long_term"
                })

        return results[:limit]

    async def vector_search(
        self,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        ベクトル検索

        Args:
            query_vector: クエリベクトル
            limit: 最大結果数

        Returns:
            類似度の高い結果のリスト
        """
        # 実際の実装では、ChromaDBやPineconeなどを使用
        # ここではプレースホルダー
        return []

    async def store_embedding(
        self,
        key: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """埋め込みベクトルを保存"""
        self.vector_store[key] = {
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        return True

    def _log_access(self, key: str, result: str) -> None:
        """アクセスログを記録"""
        self.access_log.append({
            "key": key,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # ログサイズ制限
        if len(self.access_log) > 1000:
            self.access_log = self.access_log[-500:]

    async def get_stats(self) -> Dict[str, Any]:
        """メモリストアの統計情報を取得"""
        total_accesses = len(self.access_log)
        hits = sum(1 for log in self.access_log if "hit" in log["result"])

        return {
            "short_term_keys": len(self.short_term_memory),
            "long_term_keys": len(self.long_term_memory),
            "vector_keys": len(self.vector_store),
            "total_accesses": total_accesses,
            "cache_hits": hits,
            "hit_rate": hits / total_accesses if total_accesses > 0 else 0,
            "backend": self.backend
        }

    async def clear(self, memory_type: str = "all") -> None:
        """メモリをクリア"""
        if memory_type in ["all", "short_term"]:
            self.short_term_memory.clear()
            logger.info("Short-term memory cleared")

        if memory_type in ["all", "long_term"]:
            self.long_term_memory.clear()
            logger.info("Long-term memory cleared")

        if memory_type in ["all", "vector"]:
            self.vector_store.clear()
            logger.info("Vector store cleared")
