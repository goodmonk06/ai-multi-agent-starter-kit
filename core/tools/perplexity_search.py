"""
Perplexity Search - Web検索エージェント用のPerplexity API統合

機能:
- Perplexity APIを使った高品質なWeb検索
- 1日のリクエスト数制限
- 月額利用額の制限
- メモリベースの使用量追跡
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
import httpx

logger = structlog.get_logger()


class PerplexitySearchManager:
    """Perplexity検索の使用量管理とAPI呼び出し"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_requests_per_day: Optional[int] = None,
        max_dollars_per_month: Optional[float] = None
    ):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.max_requests_per_day = max_requests_per_day or int(
            os.getenv("PERPLEXITY_MAX_REQUESTS_PER_DAY", "50")
        )
        self.max_dollars_per_month = max_dollars_per_month or float(
            os.getenv("PERPLEXITY_MAX_DOLLARS_PER_MONTH", "5.0")
        )

        # 使用量追跡（メモリベース）
        self.daily_requests = {}
        self.monthly_cost = {}
        self.current_month = datetime.now().strftime("%Y-%m")

        # Perplexity API設定
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.model = "llama-3.1-sonar-small-128k-online"  # 検索に最適なモデル

        # コスト推定（概算）
        # Perplexity Sonar Smallモデルの推定コスト: $0.20/1M tokens (input), $0.20/1M tokens (output)
        self.cost_per_1k_tokens = 0.0002  # 約$0.20/1M tokens

        logger.info(
            "PerplexitySearchManager initialized",
            max_requests_per_day=self.max_requests_per_day,
            max_dollars_per_month=self.max_dollars_per_month
        )

    def _get_today_key(self) -> str:
        """今日の日付キーを取得"""
        return datetime.now().strftime("%Y-%m-%d")

    def _cleanup_old_data(self) -> None:
        """古いデータをクリーンアップ"""
        today = self._get_today_key()
        # 過去のデータを削除（昨日以前）
        keys_to_delete = [k for k in self.daily_requests.keys() if k < today]
        for key in keys_to_delete:
            del self.daily_requests[key]

        # 月が変わったらコストをリセット
        current_month = datetime.now().strftime("%Y-%m")
        if current_month != self.current_month:
            self.monthly_cost.clear()
            self.current_month = current_month

    def _get_daily_request_count(self) -> int:
        """今日のリクエスト数を取得"""
        self._cleanup_old_data()
        today = self._get_today_key()
        return self.daily_requests.get(today, 0)

    def _get_monthly_cost(self) -> float:
        """今月の利用額を取得"""
        self._cleanup_old_data()
        return self.monthly_cost.get(self.current_month, 0.0)

    def _increment_usage(self, estimated_cost: float) -> None:
        """使用量を記録"""
        today = self._get_today_key()
        self.daily_requests[today] = self.daily_requests.get(today, 0) + 1
        self.monthly_cost[self.current_month] = (
            self.monthly_cost.get(self.current_month, 0.0) + estimated_cost
        )

    def _estimate_cost(self, max_tokens: int) -> float:
        """コストを推定"""
        # 簡易推定: input + output tokens
        # inputは平均200トークン、outputはmax_tokensと仮定
        estimated_tokens = 200 + max_tokens
        return (estimated_tokens / 1000) * self.cost_per_1k_tokens

    def check_limits(self, max_tokens: int) -> Dict[str, Any]:
        """
        リクエスト制限をチェック

        Returns:
            {"allowed": bool, "reason": str, "usage": dict}
        """
        daily_count = self._get_daily_request_count()
        monthly_cost = self._get_monthly_cost()
        estimated_cost = self._estimate_cost(max_tokens)

        # 1日のリクエスト数チェック
        if daily_count >= self.max_requests_per_day:
            return {
                "allowed": False,
                "reason": f"Daily request limit reached ({self.max_requests_per_day})",
                "usage": {
                    "daily_requests": daily_count,
                    "monthly_cost": monthly_cost
                }
            }

        # 月額利用額チェック
        if monthly_cost + estimated_cost > self.max_dollars_per_month:
            return {
                "allowed": False,
                "reason": f"Monthly budget limit reached (${self.max_dollars_per_month})",
                "usage": {
                    "daily_requests": daily_count,
                    "monthly_cost": monthly_cost
                }
            }

        return {
            "allowed": True,
            "reason": "OK",
            "usage": {
                "daily_requests": daily_count,
                "monthly_cost": monthly_cost,
                "estimated_cost": estimated_cost
            }
        }

    async def search(
        self,
        query: str,
        max_tokens: int = 512,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perplexity APIで検索を実行

        Args:
            query: 検索クエリ
            max_tokens: 最大トークン数
            system_prompt: システムプロンプト（オプション）

        Returns:
            検索結果
        """
        # 制限チェック
        limit_check = self.check_limits(max_tokens)

        if not limit_check["allowed"]:
            logger.warning(
                "Search limit reached",
                reason=limit_check["reason"],
                usage=limit_check["usage"]
            )
            return {
                "success": False,
                "error": limit_check["reason"],
                "usage": limit_check["usage"],
                "content": f"検索上限に達しました: {limit_check['reason']}"
            }

        # APIキーチェック
        if not self.api_key or self.api_key == "your-perplexity-key":
            logger.error("Perplexity API key not configured")
            return {
                "success": False,
                "error": "API key not configured",
                "content": "Perplexity APIキーが設定されていません"
            }

        # API呼び出し
        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": query
            })

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.2,
                        "return_citations": True,
                        "return_images": False
                    }
                )

                response.raise_for_status()
                result = response.json()

                # 使用量を記録
                estimated_cost = limit_check["usage"]["estimated_cost"]
                self._increment_usage(estimated_cost)

                # レスポンスを解析
                content = result["choices"][0]["message"]["content"]
                citations = result.get("citations", [])

                logger.info(
                    "Perplexity search completed",
                    query=query[:50],
                    tokens_used=result.get("usage", {}).get("total_tokens", 0),
                    citations_count=len(citations)
                )

                return {
                    "success": True,
                    "content": content,
                    "citations": citations,
                    "usage": {
                        "daily_requests": self._get_daily_request_count(),
                        "monthly_cost": self._get_monthly_cost(),
                        "tokens_used": result.get("usage", {})
                    },
                    "model": self.model
                }

        except httpx.HTTPStatusError as e:
            logger.error(
                "Perplexity API HTTP error",
                status_code=e.response.status_code,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"API HTTP error: {e.response.status_code}",
                "content": f"検索エラーが発生しました: HTTP {e.response.status_code}"
            }

        except httpx.TimeoutException:
            logger.error("Perplexity API timeout")
            return {
                "success": False,
                "error": "API timeout",
                "content": "検索がタイムアウトしました"
            }

        except Exception as e:
            logger.error("Perplexity search failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "content": f"検索エラーが発生しました: {str(e)}"
            }

    def get_usage_stats(self) -> Dict[str, Any]:
        """使用統計を取得"""
        return {
            "daily_requests": self._get_daily_request_count(),
            "max_requests_per_day": self.max_requests_per_day,
            "monthly_cost": self._get_monthly_cost(),
            "max_dollars_per_month": self.max_dollars_per_month,
            "current_month": self.current_month,
            "requests_remaining_today": max(
                0,
                self.max_requests_per_day - self._get_daily_request_count()
            ),
            "budget_remaining": max(
                0,
                self.max_dollars_per_month - self._get_monthly_cost()
            )
        }


# グローバルインスタンス（シングルトン）
_global_manager: Optional[PerplexitySearchManager] = None


def get_search_manager() -> PerplexitySearchManager:
    """グローバルな検索マネージャーを取得"""
    global _global_manager
    if _global_manager is None:
        _global_manager = PerplexitySearchManager()
    return _global_manager


async def run_perplexity_search(
    query: str,
    max_tokens: int = 512,
    system_prompt: Optional[str] = None
) -> str:
    """
    Perplexity検索を実行（シンプルなインターフェース）

    Args:
        query: 検索クエリ
        max_tokens: 最大トークン数
        system_prompt: システムプロンプト（オプション）

    Returns:
        検索結果のテキスト
    """
    manager = get_search_manager()
    result = await manager.search(query, max_tokens, system_prompt)

    if result["success"]:
        content = result["content"]

        # 引用情報を追加
        if result.get("citations"):
            content += "\n\n## 参照元\n"
            for i, citation in enumerate(result["citations"][:5], 1):
                content += f"{i}. {citation}\n"

        return content
    else:
        return result["content"]  # エラーメッセージを返す
