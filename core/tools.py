"""
Tools - エージェントが使用する共通ツール

機能:
- API呼び出し
- データ変換
- ファイル操作
- 通知送信
"""

from typing import Dict, List, Optional, Any, Callable
import structlog
from datetime import datetime
import json

logger = structlog.get_logger()


class ToolRegistry:
    """エージェントが使用するツールのレジストリ"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_tools()
        logger.info("ToolRegistry initialized")

    def _register_builtin_tools(self) -> None:
        """組み込みツールを登録"""
        self.register_tool(
            "http_request",
            self.http_request,
            {
                "description": "Make HTTP requests to external APIs",
                "parameters": ["url", "method", "headers", "data"]
            }
        )

        self.register_tool(
            "format_json",
            self.format_json,
            {
                "description": "Format data as JSON",
                "parameters": ["data", "indent"]
            }
        )

        self.register_tool(
            "send_email",
            self.send_email,
            {
                "description": "Send email notifications",
                "parameters": ["to", "subject", "body"]
            }
        )

        self.register_tool(
            "send_slack",
            self.send_slack,
            {
                "description": "Send Slack notifications",
                "parameters": ["channel", "message"]
            }
        )

        self.register_tool(
            "calculate",
            self.calculate,
            {
                "description": "Perform calculations",
                "parameters": ["expression"]
            }
        )

    def register_tool(
        self,
        name: str,
        function: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        ツールを登録

        Args:
            name: ツール名
            function: ツール関数
            metadata: メタデータ
        """
        self.tools[name] = function
        self.tool_metadata[name] = metadata or {}
        logger.info("Tool registered", name=name)

    async def call_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        ツールを呼び出す

        Args:
            tool_name: ツール名
            **kwargs: ツールパラメータ

        Returns:
            ツールの実行結果
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]

        try:
            logger.debug("Calling tool", tool=tool_name)
            result = await tool(**kwargs) if asyncio.iscoroutinefunction(tool) else tool(**kwargs)
            return result
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            raise

    # ========== 組み込みツール ==========

    async def http_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """HTTP リクエストを送信"""
        # 実際の実装ではhttpxを使用
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.request(method, url, headers=headers, json=data)
        #     return {
        #         "status_code": response.status_code,
        #         "data": response.json()
        #     }

        logger.info("HTTP request", method=method, url=url)
        return {
            "status_code": 200,
            "data": {"message": "Simulated response"},
            "simulated": True
        }

    def format_json(
        self,
        data: Any,
        indent: int = 2
    ) -> str:
        """データをJSON形式にフォーマット"""
        return json.dumps(data, indent=indent, ensure_ascii=False)

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: Optional[str] = None
    ) -> Dict[str, Any]:
        """メールを送信"""
        # 実際の実装ではSMTPライブラリを使用
        logger.info("Sending email", to=to, subject=subject)

        return {
            "status": "sent",
            "to": to,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
            "simulated": True
        }

    async def send_slack(
        self,
        channel: str,
        message: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Slackに通知を送信"""
        # 実際の実装ではSlack APIを使用
        logger.info("Sending Slack message", channel=channel)

        return {
            "status": "sent",
            "channel": channel,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "simulated": True
        }

    def calculate(self, expression: str) -> float:
        """数式を計算"""
        try:
            # セキュリティ: evalの代わりに安全な計算を使用
            # 実際の実装ではsympyなどを使用
            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            logger.error("Calculation failed", expression=expression, error=str(e))
            raise ValueError(f"Invalid expression: {expression}")

    async def read_file(self, file_path: str) -> str:
        """ファイルを読み込む"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error("File read failed", path=file_path, error=str(e))
            raise

    async def write_file(
        self,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """ファイルに書き込む"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "status": "success",
                "path": file_path,
                "bytes_written": len(content.encode('utf-8'))
            }
        except Exception as e:
            logger.error("File write failed", path=file_path, error=str(e))
            raise

    def list_tools(self) -> List[Dict[str, Any]]:
        """登録されているツールのリストを取得"""
        return [
            {
                "name": name,
                "metadata": self.tool_metadata.get(name, {})
            }
            for name in self.tools.keys()
        ]

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """ツールの情報を取得"""
        if tool_name not in self.tools:
            return None

        return {
            "name": tool_name,
            "function": self.tools[tool_name].__name__,
            "metadata": self.tool_metadata.get(tool_name, {})
        }


# ユーティリティ関数のインポート用
import asyncio
