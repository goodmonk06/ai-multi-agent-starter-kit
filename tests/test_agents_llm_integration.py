"""
Agents LLM Router Integration Tests

DRY_RUNモードで実行されるため、実際のAPI呼び出しは発生しません。
コストゼロでテストが可能です。

実行方法:
    pytest tests/test_agents_llm_integration.py -v
    pytest tests/test_agents_llm_integration.py -v -s  # 詳細出力
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from agents.generator_agent import GeneratorAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.compliance_agent import ComplianceAgent
from agents.scheduler_agent import SchedulerAgent
from agents.executor_agent import ExecutorAgent


class TestGeneratorAgentIntegration:
    """Generator Agent の LLM Router 統合テスト"""

    @pytest.mark.asyncio
    async def test_generator_initialization(self):
        """エージェントの初期化テスト"""
        agent = GeneratorAgent()
        assert agent.llm is not None
        assert agent.templates == {}

    @pytest.mark.asyncio
    async def test_sns_post_generation(self):
        """SNS投稿生成テスト"""
        agent = GeneratorAgent()

        context = {
            "topic": "AI Testing",
            "platform": "twitter"
        }

        result = await agent.generate_content(
            content_type="sns_post",
            context=context,
            style="professional"
        )

        assert result["type"] == "sns_post"
        assert result["style"] == "professional"
        assert "content" in result
        assert result["character_count"] > 0

    @pytest.mark.asyncio
    async def test_email_generation(self):
        """メール生成テスト"""
        agent = GeneratorAgent()

        context = {
            "subject": "Test Email",
            "recipient": "test@example.com"
        }

        result = await agent.generate_content(
            content_type="email",
            context=context
        )

        assert result["type"] == "email"
        assert result["subject"] == "Test Email"
        assert "body" in result


class TestAnalyzerAgentIntegration:
    """Analyzer Agent の LLM Router 統合テスト"""

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self):
        """エージェントの初期化テスト"""
        agent = AnalyzerAgent()
        assert agent.llm is not None

    @pytest.mark.asyncio
    async def test_general_analysis(self):
        """一般分析テスト"""
        agent = AnalyzerAgent()

        data = [
            {"value": 100, "date": "2024-01-01"},
            {"value": 150, "date": "2024-01-02"},
            {"value": 120, "date": "2024-01-03"},
        ]

        result = await agent.analyze_data(data, analysis_type="general")

        assert "record_count" in result
        assert result["record_count"] == 3
        assert "columns" in result
        assert "insights" in result

    @pytest.mark.asyncio
    async def test_anomaly_detection(self):
        """異常検知テスト"""
        agent = AnalyzerAgent()

        data = [
            {"id": 1, "value": 100},
            {"id": 2, "value": 105},
            {"id": 3, "value": 500},  # 異常値
        ]

        result = await agent.analyze_data(data, analysis_type="anomaly")

        assert "anomalies_detected" in result
        assert "severity" in result


class TestComplianceAgentIntegration:
    """Compliance Agent の LLM Router 統合テスト"""

    @pytest.mark.asyncio
    async def test_compliance_initialization(self):
        """エージェントの初期化テスト"""
        agent = ComplianceAgent()
        assert agent.llm is not None
        assert len(agent.rules) > 0

    @pytest.mark.asyncio
    async def test_text_compliance_safe(self):
        """安全なテキストのコンプライアンステスト"""
        agent = ComplianceAgent()

        content = "This is a safe message about technology."

        result = await agent.check_compliance(content, compliance_type="general")

        assert "passed" in result
        assert "violations" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_pii_detection(self):
        """PII検出テスト"""
        agent = ComplianceAgent()

        # PIIを含むテキスト
        content = "Contact: test@example.com"

        result = await agent.check_compliance(content)

        assert "violations" in result
        assert "passed" in result


class TestSchedulerAgentIntegration:
    """Scheduler Agent の LLM Router 統合テスト"""

    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """エージェントの初期化テスト"""
        agent = SchedulerAgent()
        assert agent.llm is not None
        assert agent.task_queue == []
        assert agent.scheduled_tasks == {}

    @pytest.mark.asyncio
    async def test_task_scheduling(self):
        """タスクスケジューリングテスト"""
        agent = SchedulerAgent()

        result = await agent.schedule_task(
            task_id="test_task_001",
            task_type="sns_post",
            priority=5
        )

        assert result["task_id"] == "test_task_001"
        assert result["task_type"] == "sns_post"
        assert result["priority"] == 5
        assert result["status"] == "scheduled"

    @pytest.mark.asyncio
    async def test_task_retrieval(self):
        """タスク取得テスト"""
        agent = SchedulerAgent()

        await agent.schedule_task(
            task_id="high_priority",
            task_type="test",
            priority=10
        )

        await agent.schedule_task(
            task_id="low_priority",
            task_type="test",
            priority=3
        )

        next_task = await agent.get_next_task()

        # 高優先度のタスクが先に取得されるべき
        assert next_task["task_id"] == "high_priority"
        assert next_task["priority"] == 10

    @pytest.mark.asyncio
    async def test_schedule_optimization(self):
        """スケジュール最適化テスト"""
        agent = SchedulerAgent()

        # 複数のタスクをスケジュール
        for i in range(3):
            await agent.schedule_task(
                task_id=f"opt_task_{i}",
                task_type="test",
                priority=5 + i,
                deadline=datetime.now() + timedelta(hours=i+1)
            )

        result = await agent.optimize_schedule()

        assert "optimized" in result
        assert "task_count" in result
        assert result["task_count"] == 3


class TestExecutorAgentIntegration:
    """Executor Agent の LLM Router 統合テスト"""

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """エージェントの初期化テスト"""
        agent = ExecutorAgent()
        assert agent.llm is not None
        assert agent.tools == {}
        assert agent.execution_history == []

    @pytest.mark.asyncio
    async def test_simple_task_execution(self):
        """シンプルなタスク実行テスト"""
        agent = ExecutorAgent()

        task = {
            "task_id": "test_exec_001",
            "task_type": "generic",
            "action": "test_action"
        }

        result = await agent.execute_task(task)

        assert result["task_id"] == "test_exec_001"
        assert result["status"] == "completed"
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_data_processing_execution(self):
        """データ処理実行テスト"""
        agent = ExecutorAgent()

        task = {
            "task_id": "data_proc_001",
            "task_type": "data_processing",
            "operation": "transform",
            "data": [{"id": 1}, {"id": 2}]
        }

        result = await agent.execute_task(task)

        assert result["status"] == "completed"
        assert "result" in result
        assert result["result"]["processed_count"] == 2

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """並列実行テスト"""
        agent = ExecutorAgent()

        tasks = [
            {"task_id": f"parallel_{i}", "task_type": "generic"}
            for i in range(3)
        ]

        results = await agent.execute_parallel(tasks)

        assert len(results) == 3
        assert all(r["status"] in ["completed", "failed"] for r in results)

    @pytest.mark.asyncio
    async def test_task_validation(self):
        """タスク妥当性チェックテスト"""
        agent = ExecutorAgent()

        task = {
            "task_id": "validation_test",
            "task_type": "api_call",
            "params": {"url": "https://example.com"}
        }

        result = await agent.validate_task(task)

        assert "validated" in result
        assert "task_id" in result
        assert result["task_id"] == "validation_test"


class TestCrossAgentIntegration:
    """エージェント間の統合テスト"""

    @pytest.mark.asyncio
    async def test_all_agents_have_llm_router(self):
        """すべてのエージェントがLLM Routerを持つことを確認"""
        generator = GeneratorAgent()
        analyzer = AnalyzerAgent()
        compliance = ComplianceAgent()
        scheduler = SchedulerAgent()
        executor = ExecutorAgent()

        agents = [generator, analyzer, compliance, scheduler, executor]

        for agent in agents:
            assert hasattr(agent, 'llm')
            assert agent.llm is not None

    @pytest.mark.asyncio
    async def test_workflow_integration(self):
        """ワークフロー統合テスト"""
        scheduler = SchedulerAgent()
        generator = GeneratorAgent()
        executor = ExecutorAgent()

        # 1. タスクをスケジュール
        scheduled_task = await scheduler.schedule_task(
            task_id="workflow_test_001",
            task_type="sns_post",
            priority=8
        )

        assert scheduled_task["status"] == "scheduled"

        # 2. コンテンツを生成
        content = await generator.generate_content(
            content_type="sns_post",
            context={"topic": "workflow test"},
            style="professional"
        )

        assert "content" in content

        # 3. タスクを実行
        execution_result = await executor.execute_task({
            "task_id": "workflow_test_001",
            "task_type": "sns_post",
            "content": content
        })

        assert execution_result["status"] == "completed"

        # 4. スケジューラーでステータス更新
        await scheduler.update_task_status(
            task_id="workflow_test_001",
            status="completed",
            result=execution_result
        )

        assert "workflow_test_001" in scheduler.scheduled_tasks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
