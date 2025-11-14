#!/usr/bin/env python3
"""
Morning Report Generator - 24時間の実行イベント集計

使い方:
    python scripts/morning_report.py

機能:
- storage/runs/*.jsonl から24時間分のイベントを集計
- Markdown形式のレポート生成 (storage/reports/YYYY-MM-DD.md)
- CSV形式のデータエクスポート (storage/reports/YYYY-MM-DD.csv)
- ジョブ別の実行統計
- エラー率・成功率の計算
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import structlog

logger = structlog.get_logger()


class MorningReportGenerator:
    """朝のレポート生成クラス"""

    def __init__(self, runs_dir: str = "storage/runs", reports_dir: str = "storage/reports"):
        self.runs_dir = Path(runs_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def collect_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        過去N時間分のイベントを収集

        Args:
            hours: 収集する時間範囲（デフォルト: 24時間）

        Returns:
            イベントのリスト
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        events = []

        if not self.runs_dir.exists():
            logger.warning("Runs directory does not exist", path=str(self.runs_dir))
            return events

        # すべてのJSONLファイルを読み込み
        for jsonl_file in sorted(self.runs_dir.glob("*.jsonl")):
            try:
                with open(jsonl_file, "r") as f:
                    for line in f:
                        if not line.strip():
                            continue

                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event.get("timestamp", ""))

                        # 指定時間範囲内のイベントのみ収集
                        if event_time >= cutoff_time:
                            events.append(event)

            except Exception as e:
                logger.error("Failed to read JSONL file", file=str(jsonl_file), error=str(e))

        logger.info("Events collected", count=len(events), hours=hours)
        return events

    def aggregate_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        イベントから統計情報を集計

        Args:
            events: イベントのリスト

        Returns:
            集計された統計情報
        """
        stats = {
            "total_events": len(events),
            "by_job": defaultdict(lambda: {"count": 0, "success": 0, "error": 0, "total_duration_ms": 0}),
            "by_status": defaultdict(int),
            "errors": [],
            "total_duration_ms": 0,
        }

        for event in events:
            job = event.get("job", "unknown")
            status = event.get("status", "unknown")
            duration_ms = event.get("duration_ms", 0)

            # ジョブ別統計
            stats["by_job"][job]["count"] += 1
            stats["by_job"][job]["total_duration_ms"] += duration_ms

            if status == "success":
                stats["by_job"][job]["success"] += 1
            elif status == "error":
                stats["by_job"][job]["error"] += 1
                stats["errors"].append({
                    "job": job,
                    "timestamp": event.get("timestamp"),
                    "result": event.get("result", {}),
                })

            # ステータス別統計
            stats["by_status"][status] += 1
            stats["total_duration_ms"] += duration_ms

        # 成功率を計算
        for job_stats in stats["by_job"].values():
            total = job_stats["count"]
            success = job_stats["success"]
            job_stats["success_rate"] = (success / total * 100) if total > 0 else 0
            job_stats["avg_duration_ms"] = (
                job_stats["total_duration_ms"] / total if total > 0 else 0
            )

        return stats

    def generate_markdown_report(self, stats: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
        """
        Markdown形式のレポートを生成

        Args:
            stats: 統計情報
            events: イベントリスト

        Returns:
            Markdownテキスト
        """
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"""# 24時間稼働レポート

**生成日時:** {report_time}
**対象期間:** 過去24時間

---

## 📊 サマリー

- **総イベント数:** {stats['total_events']}
- **総実行時間:** {stats['total_duration_ms'] / 1000:.2f}秒
- **成功:** {stats['by_status'].get('success', 0)}件
- **エラー:** {stats['by_status'].get('error', 0)}件

---

## 📈 ジョブ別統計

| ジョブ名 | 実行回数 | 成功 | エラー | 成功率 | 平均実行時間 |
|---------|---------|------|--------|--------|--------------|
"""

        for job, job_stats in sorted(stats["by_job"].items()):
            md += f"| {job} | {job_stats['count']} | {job_stats['success']} | {job_stats['error']} | {job_stats['success_rate']:.1f}% | {job_stats['avg_duration_ms']:.0f}ms |\n"

        md += "\n---\n\n"

        # エラー詳細
        if stats["errors"]:
            md += f"## ⚠️ エラー詳細 ({len(stats['errors'])}件)\n\n"

            for i, error in enumerate(stats["errors"][:10], 1):  # 最大10件表示
                md += f"### {i}. {error['job']}\n"
                md += f"- **時刻:** {error['timestamp']}\n"
                md += f"- **詳細:** {error.get('result', {})}\n\n"

            if len(stats["errors"]) > 10:
                md += f"*...他 {len(stats['errors']) - 10}件のエラー*\n\n"
        else:
            md += "## ✅ エラーなし\n\n過去24時間でエラーは発生していません。\n\n"

        md += "---\n\n"
        md += f"*Generated by AI Multi-Agent Starter Kit - {report_time}*\n"

        return md

    def generate_csv_report(self, events: List[Dict[str, Any]]) -> str:
        """
        CSV形式のレポートを生成

        Args:
            events: イベントリスト

        Returns:
            CSVテキスト
        """
        if not events:
            return "timestamp,job,status,duration_ms,dry_run\n"

        # CSV行を生成
        csv_lines = ["timestamp,job,status,duration_ms,dry_run"]

        for event in events:
            timestamp = event.get("timestamp", "")
            job = event.get("job", "unknown")
            status = event.get("status", "unknown")
            duration_ms = event.get("duration_ms", 0)
            dry_run = event.get("dry_run", True)

            csv_lines.append(f"{timestamp},{job},{status},{duration_ms},{dry_run}")

        return "\n".join(csv_lines)

    def generate_report(self, hours: int = 24) -> Dict[str, str]:
        """
        レポートを生成して保存

        Args:
            hours: 集計する時間範囲

        Returns:
            生成されたファイルパスの辞書
        """
        logger.info("Generating morning report", hours=hours)

        # イベント収集
        events = self.collect_events(hours=hours)

        if not events:
            logger.warning("No events found for report generation")
            return {"markdown": None, "csv": None}

        # 統計集計
        stats = self.aggregate_stats(events)

        # レポート生成
        report_date = datetime.now().strftime("%Y-%m-%d")

        # Markdownレポート
        md_content = self.generate_markdown_report(stats, events)
        md_path = self.reports_dir / f"{report_date}.md"

        with open(md_path, "w") as f:
            f.write(md_content)

        logger.info("Markdown report saved", path=str(md_path))

        # CSVレポート
        csv_content = self.generate_csv_report(events)
        csv_path = self.reports_dir / f"{report_date}.csv"

        with open(csv_path, "w") as f:
            f.write(csv_content)

        logger.info("CSV report saved", path=str(csv_path))

        return {
            "markdown": str(md_path),
            "csv": str(csv_path),
            "events_count": len(events),
            "stats": stats,
        }


def main():
    """メインエントリーポイント"""
    print("=" * 60)
    print("📊 Morning Report Generator")
    print("=" * 60)
    print()

    generator = MorningReportGenerator()

    try:
        result = generator.generate_report(hours=24)

        if result["markdown"] and result["csv"]:
            print(f"✅ Report generated successfully!")
            print()
            print(f"📄 Markdown: {result['markdown']}")
            print(f"📊 CSV:      {result['csv']}")
            print()
            print(f"📈 Events processed: {result['events_count']}")
            print()

            # サマリー表示
            stats = result["stats"]
            print("Summary:")
            print(f"  Total events: {stats['total_events']}")
            print(f"  Success:      {stats['by_status'].get('success', 0)}")
            print(f"  Errors:       {stats['by_status'].get('error', 0)}")
            print()

        else:
            print("⚠️  No events found for report generation")
            print()
            print("Make sure the runner is enabled and has executed jobs.")
            print()

    except Exception as e:
        logger.error("Report generation failed", error=str(e))
        print(f"❌ Error: {str(e)}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    main()
