"""
AI Multi-Agent Starter Kit - Agents Module

This module contains specialized agents for different tasks:
- scheduler_agent: Schedule and manage tasks
- analyzer_agent: Analyze data and provide insights
- generator_agent: Generate content and responses
- compliance_agent: Check compliance and regulations
- executor_agent: Execute tasks and workflows
"""

from .scheduler_agent import SchedulerAgent
from .analyzer_agent import AnalyzerAgent
from .generator_agent import GeneratorAgent
from .compliance_agent import ComplianceAgent
from .executor_agent import ExecutorAgent

__all__ = [
    "SchedulerAgent",
    "AnalyzerAgent",
    "GeneratorAgent",
    "ComplianceAgent",
    "ExecutorAgent",
]
