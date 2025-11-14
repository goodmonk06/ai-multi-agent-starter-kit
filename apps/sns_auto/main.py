"""
SNS Auto Application - メインアプリケーション

機能:
- 投稿スケジューリング
- コンテンツ生成
- エンゲージメント分析
- 自動返信
"""

from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()


class SnsAutoApp:
    """SNS自動化アプリケーション"""

    def __init__(self, agents: Dict[str, Any], workflow, memory):
        self.agents = agents
        self.workflow = workflow
        self.memory = memory
        self.scheduled_posts = {}
        logger.info("SnsAutoApp initialized")

    async def create_post(
        self,
        platform: str,
        topic: str,
        style: str = "professional",
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        SNS投稿を作成

        Args:
            platform: プラットフォーム (twitter, facebook, instagram, linkedin)
            topic: トピック
            style: スタイル
            hashtags: ハッシュタグ
            schedule_time: 投稿予定時刻

        Returns:
            作成された投稿
        """
        logger.info(
            "Creating SNS post",
            platform=platform,
            topic=topic,
            style=style
        )

        generator = self.agents.get("generator")
        compliance = self.agents.get("compliance")

        # コンテンツ生成
        if not generator:
            return {"error": "Generator agent not available"}

        # プラットフォーム別の最大文字数
        max_lengths = {
            "twitter": 280,
            "facebook": 5000,
            "instagram": 2200,
            "linkedin": 3000
        }

        max_length = max_lengths.get(platform, 280)

        content_context = {
            "topic": topic,
            "platform": platform,
            "audience": self._get_platform_audience(platform),
            "tone": style,
            "key_points": [topic]
        }

        if hashtags:
            content_context["hashtags"] = hashtags

        generated = await generator.generate_content(
            content_type="sns_post",
            context=content_context,
            style=style,
            max_length=max_length
        )

        # コンプライアンスチェック
        if compliance:
            compliance_check = await compliance.check_compliance(
                generated.get("content", ""),
                compliance_type="content_policy"
            )

            if not compliance_check.get("passed"):
                logger.warning(
                    "Compliance check failed",
                    violations=compliance_check.get("violations")
                )

                # 違反がある場合は修正を試みる
                generated["compliance_issues"] = compliance_check["violations"]
                generated["status"] = "needs_review"
            else:
                generated["status"] = "approved"
        else:
            generated["status"] = "pending"

        # 投稿データを構築
        post_id = f"post_{platform}_{datetime.now().timestamp()}"

        post_data = {
            "post_id": post_id,
            "platform": platform,
            "content": generated.get("content"),
            "hashtags": generated.get("hashtags", hashtags or []),
            "topic": topic,
            "style": style,
            "status": generated.get("status"),
            "created_at": datetime.now().isoformat(),
            "scheduled_time": schedule_time.isoformat() if schedule_time else None,
            "posted_at": None
        }

        # スケジュール登録
        if schedule_time:
            scheduler = self.agents.get("scheduler")
            if scheduler:
                await scheduler.schedule_task(
                    task_id=post_id,
                    task_type="sns_post",
                    priority=5,
                    deadline=schedule_time,
                    metadata=post_data
                )

        self.scheduled_posts[post_id] = post_data

        # メモリに保存
        if self.memory:
            await self.memory.store(f"sns_post:{post_id}", post_data)

        return post_data

    async def analyze_engagement(
        self,
        platform: str,
        time_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        エンゲージメントを分析

        Args:
            platform: プラットフォーム
            time_range: 時間範囲 {"start": "2024-01-01", "end": "2024-01-31"}

        Returns:
            エンゲージメント分析結果
        """
        logger.info(
            "Analyzing engagement",
            platform=platform,
            range=time_range
        )

        analyzer = self.agents.get("analyzer")

        if not analyzer:
            return {"error": "Analyzer agent not available"}

        # 過去の投稿データを取得
        historical_posts = await self._get_posts_in_range(
            platform,
            time_range
        )

        # エンゲージメントデータを分析
        analysis = await analyzer.analyze_data(
            historical_posts,
            analysis_type="trend"
        )

        # インサイトを追加
        insights = self._generate_engagement_insights(
            historical_posts,
            analysis
        )

        analysis["insights"] = insights
        analysis["platform"] = platform
        analysis["time_range"] = time_range

        return analysis

    async def auto_reply(
        self,
        platform: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        自動返信

        Args:
            platform: プラットフォーム
            message: 受信メッセージ

        Returns:
            返信内容
        """
        logger.info("Generating auto reply", platform=platform)

        generator = self.agents.get("generator")
        compliance = self.agents.get("compliance")

        if not generator:
            return {"error": "Generator agent not available"}

        # 返信を生成
        reply_context = {
            "purpose": "reply_to_message",
            "original_message": message.get("content"),
            "sender": message.get("sender"),
            "platform": platform,
            "tone": "friendly"
        }

        reply = await generator.generate_content(
            content_type="message",
            context=reply_context,
            style="friendly"
        )

        # コンプライアンスチェック
        if compliance:
            check = await compliance.check_compliance(
                reply.get("content"),
                compliance_type="content_policy"
            )

            if check.get("passed"):
                reply["status"] = "approved"
            else:
                reply["status"] = "needs_review"
                reply["compliance_issues"] = check["violations"]

        reply["platform"] = platform
        reply["in_reply_to"] = message.get("message_id")

        return reply

    async def schedule_campaign(
        self,
        campaign_name: str,
        platforms: List[str],
        posts: List[Dict[str, Any]],
        schedule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        キャンペーンをスケジュール

        Args:
            campaign_name: キャンペーン名
            platforms: プラットフォームリスト
            posts: 投稿リスト
            schedule: スケジュール設定

        Returns:
            キャンペーン情報
        """
        logger.info(
            "Scheduling campaign",
            name=campaign_name,
            platforms=platforms
        )

        scheduler = self.agents.get("scheduler")

        campaign_id = f"campaign_{datetime.now().timestamp()}"

        campaign = {
            "campaign_id": campaign_id,
            "name": campaign_name,
            "platforms": platforms,
            "posts": [],
            "schedule": schedule,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        # 各投稿をスケジュール
        for i, post_data in enumerate(posts):
            for platform in platforms:
                post = await self.create_post(
                    platform=platform,
                    topic=post_data.get("topic"),
                    style=post_data.get("style", "professional"),
                    hashtags=post_data.get("hashtags"),
                    schedule_time=self._calculate_post_time(schedule, i)
                )

                campaign["posts"].append(post)

        # メモリに保存
        if self.memory:
            await self.memory.store(f"campaign:{campaign_id}", campaign)

        return campaign

    def _get_platform_audience(self, platform: str) -> str:
        """プラットフォーム別のオーディエンスを取得"""
        audiences = {
            "twitter": "tech-savvy, news-oriented",
            "facebook": "general public, diverse age groups",
            "instagram": "visual-focused, younger demographic",
            "linkedin": "professionals, B2B"
        }
        return audiences.get(platform, "general")

    async def _get_posts_in_range(
        self,
        platform: str,
        time_range: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """期間内の投稿を取得"""
        if self.memory:
            posts = await self.memory.search(f"sns_post:{platform}", limit=100)
            return posts

        return []

    def _generate_engagement_insights(
        self,
        posts: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> List[str]:
        """エンゲージメントインサイトを生成"""
        insights = []

        if posts:
            insights.append(f"Analyzed {len(posts)} posts")

            # 最もパフォーマンスの良い投稿タイプを特定
            insights.append("Consider posting during peak engagement times")

        return insights

    def _calculate_post_time(
        self,
        schedule: Dict[str, Any],
        index: int
    ) -> datetime:
        """投稿時刻を計算"""
        start_time = datetime.fromisoformat(schedule.get("start_time", datetime.now().isoformat()))
        interval_hours = schedule.get("interval_hours", 24)

        return start_time + timedelta(hours=interval_hours * index)
