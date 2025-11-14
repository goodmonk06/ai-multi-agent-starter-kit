"""
Search Agent - Web検索を担当するエージェント

機能:
- Perplexity APIを使った高品質なWeb検索
- 検索結果の要約と構造化
- 他のエージェントへの情報提供
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime

logger = structlog.get_logger()


class SearchAgent:
    """Web検索を実行し、情報を収集するエージェント"""

    def __init__(self, memory_store=None):
        self.memory = memory_store
        self.search_history = []
        logger.info("SearchAgent initialized")

    async def search(
        self,
        query: str,
        max_tokens: int = 512,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Web検索を実行

        Args:
            query: 検索クエリ
            max_tokens: 最大トークン数
            context: 追加コンテキスト

        Returns:
            検索結果
        """
        from core.tools import run_perplexity_search

        logger.info("Executing search", query=query[:50])

        search_id = f"search_{datetime.now().timestamp()}"

        try:
            # システムプロンプトを構築
            system_prompt = self._build_system_prompt(context)

            # Perplexity検索を実行
            result_text = await run_perplexity_search(
                query=query,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )

            search_result = {
                "search_id": search_id,
                "query": query,
                "result": result_text,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "context": context or {}
            }

            # 検索履歴に追加
            self.search_history.append(search_result)

            # メモリに保存
            if self.memory:
                await self.memory.store(f"search:{search_id}", search_result)

            logger.info("Search completed", search_id=search_id, query=query[:50])

            return search_result

        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))

            error_result = {
                "search_id": search_id,
                "query": query,
                "result": f"検索エラー: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
                "context": context or {}
            }

            self.search_history.append(error_result)

            return error_result

    async def multi_search(
        self,
        queries: List[str],
        max_tokens: int = 512
    ) -> List[Dict[str, Any]]:
        """
        複数のクエリで検索を実行

        Args:
            queries: 検索クエリのリスト
            max_tokens: 最大トークン数

        Returns:
            検索結果のリスト
        """
        logger.info("Executing multi-search", query_count=len(queries))

        results = []
        for query in queries:
            result = await self.search(query, max_tokens)
            results.append(result)

        return results

    async def search_and_summarize(
        self,
        query: str,
        summarize_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        検索して結果を要約

        Args:
            query: 検索クエリ
            summarize_prompt: 要約用のプロンプト

        Returns:
            検索結果と要約
        """
        # 検索を実行
        search_result = await self.search(query)

        if search_result["status"] != "success":
            return search_result

        # 要約（実装例：簡易的な要約）
        summary = self._extract_summary(search_result["result"])

        search_result["summary"] = summary

        # メモリを更新
        if self.memory:
            await self.memory.store(
                f"search:{search_result['search_id']}",
                search_result
            )

        return search_result

    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """システムプロンプトを構築"""
        base_prompt = (
            "あなたは正確で信頼性の高い情報を提供する検索アシスタントです。\n"
            "検索結果は簡潔かつ構造化された形式で提供してください。\n"
            "情報源は必ず明記してください。"
        )

        if context:
            if "domain" in context:
                base_prompt += f"\n専門分野: {context['domain']}"

            if "audience" in context:
                base_prompt += f"\n対象者: {context['audience']}"

            if "purpose" in context:
                base_prompt += f"\n目的: {context['purpose']}"

        return base_prompt

    def _extract_summary(self, text: str, max_length: int = 300) -> str:
        """テキストから要約を抽出"""
        # シンプルな要約：最初のN文字
        if len(text) <= max_length:
            return text

        # 文の途中で切らないように、最後のピリオドまで
        summary = text[:max_length]
        last_period = summary.rfind("。")
        if last_period > 0:
            summary = summary[:last_period + 1]

        return summary + "..."

    async def get_search_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """検索履歴を取得"""
        return self.search_history[-limit:]

    async def get_usage_stats(self) -> Dict[str, Any]:
        """使用統計を取得"""
        from core.tools import get_search_manager

        manager = get_search_manager()
        usage_stats = manager.get_usage_stats()

        stats = {
            "total_searches": len(self.search_history),
            "successful_searches": sum(
                1 for s in self.search_history if s["status"] == "success"
            ),
            "failed_searches": sum(
                1 for s in self.search_history if s["status"] == "error"
            ),
            "perplexity_usage": usage_stats
        }

        return stats

    async def search_for_topic(
        self,
        topic: str,
        aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        トピックに関する包括的な検索

        Args:
            topic: トピック
            aspects: 調査する側面のリスト

        Returns:
            検索結果の統合
        """
        logger.info("Searching for topic", topic=topic)

        # デフォルトの調査側面
        if not aspects:
            aspects = ["overview", "latest_trends", "best_practices"]

        # 各側面について検索
        results = {}
        for aspect in aspects:
            query = f"{topic}について、{aspect}の観点から詳しく教えてください"
            result = await self.search(query, max_tokens=512)
            results[aspect] = result

        # 統合結果を作成
        integrated_result = {
            "topic": topic,
            "aspects": aspects,
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "summary": self._integrate_results(results)
        }

        return integrated_result

    def _integrate_results(self, results: Dict[str, Dict[str, Any]]) -> str:
        """複数の検索結果を統合"""
        integrated = f"# 検索結果統合\n\n"

        for aspect, result in results.items():
            if result["status"] == "success":
                integrated += f"## {aspect}\n\n"
                integrated += result.get("summary", result["result"][:500])
                integrated += "\n\n"

        return integrated

    async def clear_history(self) -> None:
        """検索履歴をクリア"""
        self.search_history.clear()
        logger.info("Search history cleared")
